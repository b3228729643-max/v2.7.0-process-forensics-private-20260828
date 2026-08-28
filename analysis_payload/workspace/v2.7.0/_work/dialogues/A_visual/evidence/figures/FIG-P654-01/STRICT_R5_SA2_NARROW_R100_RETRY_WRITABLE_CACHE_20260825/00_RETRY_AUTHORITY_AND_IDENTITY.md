# FIG-P654-01 R5 narrow retry — authority and identity

- `BUILD_AUTHORITY`: explicit mainline `P654_RETRY_BUILD_SLOT_GRANTED`
- `FIGURE_ID`: `FIG-P654-01`
- `ROLE`: `SA2=gpt-5.6-sol/max`
- `TARGET_OBJECT`: `FRM_TRIAL_005`
- `TARGET_SOURCE`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex`
- `TARGET_SOURCE_SHA256`: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- `SOURCE_PATCH`: only the line-22 standalone `\boldsymbol n` is locally typeset at `10.7pt/12.2pt`; no additional source change occurred in R5
- `PRECHECK`: latexmk/lualatex/luatex/luahbtex all `NONE`
- `INVOCATION_LIMIT`: one retry controller with natural internal passes only; no third build permitted

The accepted R100 failure remains `FRM_TRIAL_005 H_INK=21px<22px`. R5 is a build retry for the unchanged narrow source patch, not a fresh audit role.
