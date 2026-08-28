# LaTeX公共模板

`statlearnbook.sty` 是五册讲义唯一公共样式入口。它固定：

- XeLaTeX、A4页面、页边距、页眉页脚与目录层级；
- SimSun正文、SimHei中文标题、Times New Roman英文、TeX Gyre Termes Math数学字体；
- 按章编号的公式、图、表、算法、定义、定理、例题和练习；
- 统一的定义/定理/例题/练习及前置知识、依赖图、自检环境；
- PDF书签、交叉引用、主题索引与符号索引。

各册和各章不得重复定义公共命令。若需新增通用环境，统一修改本文件并复编五册。

编译时使用同目录的 `latexmkrc`，其中把Unicode主题/符号索引交给 `upmendex`：

```powershell
latexmk -r ../common/latexmkrc -xelatex -interaction=nonstopmode -halt-on-error main.tex
```
