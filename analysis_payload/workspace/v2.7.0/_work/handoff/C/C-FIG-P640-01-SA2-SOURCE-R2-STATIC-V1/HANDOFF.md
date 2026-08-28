# FIG-P640-01 SOURCE R2 static freeze

- HANDOFF_ID: `C-FIG-P640-01-SA2-SOURCE-R2-STATIC-V1`
- STATUS: `SOURCE_STATIC_READY_REQUEST_BUILD_SLOT`
- WORKTREE: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual`
- WORKTREE_HEAD: `95ab454ce5846daba9b33dda2d5f68a6f993a1ef`
- SOURCE_PATH: `src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_mixing_rho_comparison.tex`
- SOURCE_BYTES: `2717`
- SOURCE_R2_SHA256: `044431D3E6B2ABAFE786EB151B7F4B01585F8E83F158EADEF736E005F6161F38`
- SOURCE_R1_SHA256: `FFAE906011BBAD21FD1AD53997693934828394C2AE516649CCCF8DA5938D9B89`
- TEX_STATUS: `DISABLED`
- COMMIT_STATUS: `NOT_AUTHORIZED`

## Exact authorized increment

Relative to the accepted R1 source, exactly one unique token changed:

```diff
- width=4.9cm,height=4.2cm,xmin=0,xmax=.99,ymin=-.04,ymax=1,
+ width=4.9cm,height=4.2cm,xmin=0,xmax=.99,ymin=-.06,ymax=1,
```

In-memory reverse replacement of the unique `ymin=-.06` reproduces the 2,717-byte R1 source SHA-256 exactly. Current counts are `ymin=-.06`: 1 and `ymin=-.04`: 0.

Relative to worktree HEAD, the cumulative Git diff remains exactly the same one P640 source file and one changed line: `ymin=0` to `ymin=-.06`, with diffstat 1 insertion / 1 deletion. `git diff --check` passes.

## Preserved gates

- `.99` remains in both `xtick={0,.5,.99}` and `xticklabels={0,.5,.99}`.
- The true point remains `coordinates {(.99,0.0100499975)}`.
- The displayed `$(.99,\,.010)$` label remains at that same data coordinate.
- `axis lines=left`, the ESS curve, formula, sampling, marker style, limit annotation, mathematics, caption, panel size and all left-panel bytes remain unchanged relative to R1.
- No second source including P639 was modified.

## Static prediction only

The R1 vector geometry implies a 3px native300dpi threshold at `ymin <= -0.055951065`. The selected `-.06` predicts marker center `179.488000pt`, marker bottom `181.281297pt`, and tick-to-marker clearance `0.985793pt = 4.107px`. This is not a PASS claim; only a newly authorized candidate build and non-TeX measurement may decide the geometry gate.

No LuaLaTeX, latexmk, retry, commit, fresh role, central state write or inventory write was performed.
