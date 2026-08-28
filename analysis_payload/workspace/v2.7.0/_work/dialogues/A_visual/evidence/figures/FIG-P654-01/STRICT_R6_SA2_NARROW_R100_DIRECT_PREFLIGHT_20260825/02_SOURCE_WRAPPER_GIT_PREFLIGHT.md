# Wrapper, source and Git-scope preflight

- `WRAPPER`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P654-01_standalone.tex`
- `WRAPPER_BYTES`: `397`
- `WRAPPER_SHA256`: `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`
- `WRAPPER_GIT_DIFF`: none; `git diff --quiet` exit 0
- `TARGET_SOURCE`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex`
- `TARGET_SOURCE_BYTES`: `3122`
- `TARGET_SOURCE_SHA256`: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`

Git scope is exactly one tracked modified file: the authorized target source. `git diff --numstat` is exactly `1 insertion / 1 deletion`; `git diff --check` exits 0. The exact change remains:

```diff
-\node[aux,text width=28mm] (trial) at (-5.499,1.15) {类别计数\\$\boldsymbol n$};
+\node[aux,text width=28mm] (trial) at (-5.499,1.15) {类别计数\\{\fontsize{10.7pt}{12.2pt}\selectfont$\boldsymbol n$}};
```

No wrapper, second source, shared macro/style/index/build entry or old sealed evidence root was changed.
