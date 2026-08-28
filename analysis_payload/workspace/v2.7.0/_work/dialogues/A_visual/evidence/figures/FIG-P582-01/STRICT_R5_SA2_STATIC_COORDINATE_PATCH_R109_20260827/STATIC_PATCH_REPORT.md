# FIG-P582-01 R109 SA2 static coordinate patch

- HANDOFF_ID: `A-R109-P582-SA2-STATIC-COORDINATE-PATCH-20260827`
- Route: `P582_SOURCE_COORDINATE_PATCH_READY_REQUEST_BUILD_SLOT`
- Scope: exactly one source file and one coordinate literal.
- TeX invocations: 0.
- Commits: 0.

## Identity and exact change

- Source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_running_mean.tex`
- Before SHA-256: `4AB4E8D14252B20576F05BD1D5CB54BCB28F162B9E33EF439BD3ED6E01DBC65C`
- After SHA-256: `989E12DFD1B7A7F58A7953F36A8E8F24427A56154EED33325262045C17583A57`
- Bytes: `2627 -> 2627`
- Numstat: `1 insertion / 1 deletion`
- `git diff --check`: PASS (exit 0)
- Old literal count after patch: 0.
- New literal count after patch: 1.

The only change is:

```tex
- at (axis cs:3.58,.49) {$\downarrow$ 再下降};
+ at (axis cs:3.58,.53) {$\downarrow$ 再下降};
```

## Static mechanism and risk

The annotation keeps `x=3.58`, its text, font, color and mathematical arrow unchanged. Raising its y coordinate by `0.04` increases the intended vertical separation from the `.380` terminal digit that fresh SA3 found to have 14 native-300-dpi shared pixels with the down arrow.

No data point, running-mean value, axis, curve, formula, reference line, label text or other coordinate changed. The new y coordinate `.53` remains inside the unchanged `ymax=.70`. The primary regression risk is a new proximity to upper plot content; this cannot be closed statically and must be measured from one newly built PDF. That build must remeasure P05555 and rerun the full-figure native geometry/semantic gates without reusing R4 manual conclusions.

## Boundary

No LuaLaTeX/latexmk was started. No commit, fresh role, second UID, central state or inventory write occurred. The worktree has exactly this one modified source file.
