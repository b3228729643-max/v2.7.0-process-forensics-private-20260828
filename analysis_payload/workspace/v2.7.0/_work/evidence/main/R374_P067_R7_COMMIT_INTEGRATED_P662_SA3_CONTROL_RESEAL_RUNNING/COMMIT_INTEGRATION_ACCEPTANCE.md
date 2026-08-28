# R374 P067 R7 atomic commit integration acceptance

时间：2026-08-27T17:34:13+08:00

- A授权提交=`3c371f2448c86686ef5fc198237a395f9c4668e1`，parent=`ab199fc685753015c3aa4d930ea1217e80aedf63`，subject=`fix(fig-p067): align CDF steps with right-continuous values`。
- 主线独立核对commit object：name-only恰 `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`；numstat恰1+/1-；唯一diff=`const plot mark right`→`const plot mark left`；diff-check PASS。
- A worktree HEAD精确命中、postcommit status clean；source4014 bytes/SHA-256=`2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920`。不可变handoff 1289 bytes/SHA-256=`1C6346C23C83ADB11BFE8B93F06246F02DEE77FBAEC462D77FDDC2D9A4CC24F5`，ReadOnly。
- 从clean main HEAD=`27fca4d1a0c9034807a161c1bffa4f4d8f099339`执行唯一cherry-pick，自然成功为main commit=`3bc644256d833272a789a7685b91996f98fa3336`；main commit仍name-only同一目标源、numstat1+/1-、source bytes/SHA精确，postintegration worktree/index clean，TeX-family process count0。
- 未push、未产生第二commit、未启动TeX/build/fresh role/第二UID。R112保持旧唯一官方候选，已不包含main新commit；新官方候选仅在P662 control reseal独立验收及后续显式build lock后发布。
- P067永久冻结为已集成LOCAL_SA2_PASS，等待下一官方候选fresh复验；P662唯一control reseal授权继续，不受本次Git集成影响。

inventory保持 `31 SA1 / 38 SA2 / 1 SA3 / 30 local pass`。
