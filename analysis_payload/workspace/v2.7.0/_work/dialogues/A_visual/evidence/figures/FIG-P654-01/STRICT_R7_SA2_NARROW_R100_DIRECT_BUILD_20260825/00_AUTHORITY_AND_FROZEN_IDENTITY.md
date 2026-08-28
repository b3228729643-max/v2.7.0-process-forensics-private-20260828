# P654 R7 direct-build authority and frozen identity

- `AUTHORITY`: `P654_R7_DIRECT_BUILD_SLOT_GRANTED` from mainline.
- `ALLOWED_TEX_CONTROLLER_COUNT`: exactly one direct `lualatex` invocation; no `latexmk`, concurrency or automatic retry.
- `PRECHECK`: `latexmk` / `lualatex` / `luatex` / `luahbtex` processes were all `NONE` immediately before creating this package.
- `SOURCE`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex`
- `SOURCE_SHA256`: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- `SOURCE_BYTES`: `3122`
- `WRAPPER`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P654-01_standalone.tex`
- `WRAPPER_SHA256`: `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`
- `WRAPPER_BYTES`: `397`
- `GIT_SCOPE`: exactly the target source, `1 insertion / 1 deletion`; `git diff --check` exit 0.

The R6 diagnostic package is sealed and remains read-only. R7 uses its own unique `texcache` and `build` directories.
