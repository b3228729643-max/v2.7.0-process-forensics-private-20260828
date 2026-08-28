# Exact authorized business-source diff

- `BEFORE_SOURCE_SHA256`: `8041DAF98B04D763958DA9C83AF3472FA346D003F0FDCEF13A42FE1AA046B5F8`
- `AFTER_SOURCE_SHA256`: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- `SOURCE_SCOPE`: only `fig_v5_c05_dependency_graph.tex`
- `GIT_NUMSTAT`: `1 insertion / 1 deletion`
- `GIT_DIFF_CHECK`: exit 0

```diff
-\node[aux,text width=28mm] (trial) at (-5.499,1.15) {类别计数\\$\boldsymbol n$};
+\node[aux,text width=28mm] (trial) at (-5.499,1.15) {类别计数\\{\fontsize{10.7pt}{12.2pt}\selectfont$\boldsymbol n$}};
```

The node identity, coordinate, style, width, text, mathematical symbol, bold-math semantics, and all graph geometry remain unchanged. The only typesetting change is the local formula font command around mathematical `n`.
