# R315 — P049 集成与 R111 唯一全书构建锁

- 时间：2026-08-27T07:09:15+08:00
- 主线：`v2.7.0/integration`

## P049 原子提交集成

- A commit=`d8f1e5fb15abdf09ce5ead5245c270b43abd5741`，parent=`cebbb66c4f1f9cf5259f47bef0f3263dc4d50e21`，subject=`fix(fig-p049): route guide to outer contour`。
- commit exact name-only恰`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C03/fig_v1_c03_gradient_contour.tex`，numstat=`1+/1-`，`git show --check` PASS。
- 主线从clean HEAD `96ad9145d4ae47d95e1ebf4a93339ff337fcc74b` cherry-pick成功；new HEAD=`b819e9f4810a2afc04d24a2f0b8bdaa2a3ccb079`，worktree clean。
- main P049 source SHA-256=`27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E`。

## R111 唯一全书构建锁

- R111必须来自上述clean integrated HEAD。
- 唯一父调用计划：`build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r111_fullbook -NoPublish`。
- 启动前：R111 output root不存在，build script存在，`latexmk/lualatex/luatex/luahbtex=NONE`，main worktree clean。
- 禁止第二父调用、retry、Resume、A/B/C并发TeX、源码写入或中止；失败/平台中断须原样冻结后裁决。
- P641 R110 fresh isolated SA3可继续纯只读并行，不得触碰R111构建链。
- R111自然结束后立即释放构建锁，再冻结PDF/log/index/页尺寸/字体/导航与目标官方页身份。

inventory=`31 SA1 / 43 SA2 / 1 SA3 / 24 local pass`；严格最终仍为`0/99`。

