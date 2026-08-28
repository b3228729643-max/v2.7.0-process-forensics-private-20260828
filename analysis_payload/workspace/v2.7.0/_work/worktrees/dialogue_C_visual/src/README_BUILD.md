# 《统计学习方法初学者讲义》v2.7.0 构建说明

## 环境

- Windows PowerShell 5.1 或更高版本；
- TeX Live 2026（或功能等价发行版）；
- `latexmk`、LuaLaTeX、XeLaTeX、`makeindex`；
- 默认使用 LuaLaTeX。XeLaTeX 仅作为兼容回退；
- 不需要下载或复制字体。源码按 Source Han、Noto、Fandol 顺序回退，西文与数学优先 STIX Two。

构建脚本只读取 `latex_source` 内的源码，并把中间文件放在各主文件旁的
`.slbuild-<target>-<engine>` 目录，正式输出写入指定的 `build-output` 子目录。
LuaLaTeX 字体缓存位于系统临时目录中的 ASCII 路径，不进入发布包。

## 一键构建

在本文件所在目录打开 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target merged_full -Engine lualatex -OutputDir build-output\merged_full
```

完整解析版输出为：

```text
build-output\merged_full\main_full.pdf
```

其他可用目标：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target volume1 -Engine lualatex
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target volume2 -Engine lualatex
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target volume3 -Engine lualatex
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target volume4 -Engine lualatex
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target volume5 -Engine lualatex
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target merged -Engine lualatex
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target merged_student -Engine lualatex
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target demo -Engine lualatex
```

如 LuaLaTeX 在旧环境中不可用，可显式改用 `-Engine xelatex`。构建脚本会运行
足够轮次以生成目录、索引和交叉引用；任何 LaTeX 致命错误都会返回非零退出码。

若长篇合并构建被外部超时中断，可在确认没有残留 TeX 进程后，对同一目标、引擎
和输出目录增加 `-Resume`。该开关复用既有 `.slbuild-*`，并取消 `latexmk -g`
的强制全量重做；它不会绕过 LaTeX 对未收敛引用的正常重跑判断。

## 可复现检查

1. 连续执行两次 `merged_full` 命令；
2. 比较两次页数、书签、交叉引用和日志中的硬错误计数；
3. 检查合并日志、字体嵌入、链接、书签与最终页数；
4. 正式发布文件只由源码包根目录的 `build_v2.7.0.ps1` 生成。

源码包的推荐入口与发布文件名见顶层 `README_v2.7.0.md`。发布版本只在 `manifests\release_version.tex` 定义，构建脚本与 LaTeX 共用该变量。
