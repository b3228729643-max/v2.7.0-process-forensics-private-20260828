# FIG-P640-01 SA2 static geometry patch report

- return token: `P640_SOURCE_GEOMETRY_PATCH_READY_REQUEST_BUILD_SLOT`
- worktree: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual`
- worktree HEAD: `95ab454ce5846daba9b33dda2d5f68a6f993a1ef`
- writable source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_mixing_rho_comparison.tex`
- before SHA256: `C684E4CF51D41C1C550D14077DEBB59D82AD0B423640F15EAC82BE1898C90D84`
- after SHA256: `FFAE906011BBAD21FD1AD53997693934828394C2AE516649CCCF8DA5938D9B89`
- after bytes: `2717`
- diff scope: one authorized file, one insertion, one deletion
- `git diff --check`: `PASS`
- TeX processes at freeze: `NONE`
- TeX/latexmk invocation: `0`
- commit: `NONE`

## Exact patch

```diff
-  width=4.9cm,height=4.2cm,xmin=0,xmax=.99,ymin=0,ymax=1,
+  width=4.9cm,height=4.2cm,xmin=0,xmax=.99,ymin=-.04,ymax=1,
```

## Narrow closure mechanism

The failed point remains exactly `(.99,0.0100499975)` and its visible label remains `(.99,.010)`. The right-panel function, curve domain, x-domain, ticks, panel title, formulas, annotation, caption, source label, and all left-panel material are byte-identical to the pre-patch source.

Changing only the lower displayed y-domain boundary adds a four-percent empty visual margin below zero. The bottom x-axis line and its positive endpoint arrow are therefore moved below the low-valued `.99` marker while the data coordinate and the mathematical function remain unchanged. This directly targets the accepted `PAIR_0779` axis/marker collision without moving or falsifying the point.

## Static invariants

- true point `(.99,0.0100499975)`: preserved
- visible `(.99,.010)` label: preserved
- function `(1-x^2)/(1+x^2)`: preserved
- curve domain `0:.99`: preserved
- x-domain and `.99` tick: preserved
- formula, panel structure, neighboring layout source, caption and label: preserved
- threshold/taxonomy relaxation: none
- source files changed outside the authorized P640 file: none

## Residual build-time risks

Only a controlled build can prove that the native-300dpi separated masks now give `PAIR_0779 overlap=0`. The candidate must also confirm that the four-percent lower margin does not create visible imbalance, misleading negative ticks, clipping, or a new overlap. A failed build or failed visual gate must stop the chain; this static report does not claim a rendered PASS.
