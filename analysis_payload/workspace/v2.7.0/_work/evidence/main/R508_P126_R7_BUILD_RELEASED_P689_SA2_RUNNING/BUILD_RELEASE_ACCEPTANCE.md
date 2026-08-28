# R508：P126 R7 唯一构建释放验收

时间：2026-08-28T12:04:08+08:00  
HANDOFF_ID=`A-R115-P126-SA2-DIRECT-BUILD-R7-20260828`

Main以root-external只读方式接受本次构建释放：

- controller PID=7524，direct LuaLaTeX child PID=22760；controller/child exit=`0/0`，natural=true，interrupted=false。
- controller/typeset invocation=`1/1`；retry/latexmk/version-probe/second invocation=`0/0/0/0`。
- `TEXMFVAR=TEXMFCACHE=TEXMFCONFIG=TEXMFHOME`均解析到R7固定根内同一fresh `texcache`。
- preflight与terminal latexmk/lualatex/luatex/luahbtex均`0/0/0/0`；Main即时复查终态亦为`0/0/0/0`。
- R7 build目录PDF count=1；唯一PDF为`build/v260_FIG-P126-01_standalone.pdf`，33,952 bytes，SHA-256 `8EB275DEB382AD25E26C19F4B9A0EFBE01771317FE7DE475C5F2E330BCD789D6`。
- source 4,366 bytes/SHA `20671687B41E0DD6C8D36774A7E669B0ABC55C5BBE8955BE39FA69137F52F279`、wrapper 395 bytes/SHA `706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124`、controller 8,215 bytes/SHA `AC2AC0759AA18B2DC788CACAF292479F03462A345D4B1F18EE8FD9CADE2B4689`、engine 6,656 bytes/SHA `CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6`前后相同。

构建槽已释放并关闭。A现仅获准从该唯一PDF完成一次非TeX全量denominator/all-pairs、真实post-observation manual、native1x+NN8x、彩色/灰度legend run、overlap/clip、数学语义、caption/page回归与single legal seal。未授权第二构建、source新改动、commit或fresh role。

P689同一accepted-gate R115 R168 SA2实例继续运行；inventory保持`30 SA1 / 31 SA2 / 0 SA3 / 39 local pass`，严格最终`0/99`。
