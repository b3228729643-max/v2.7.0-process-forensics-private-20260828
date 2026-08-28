# v1.8.0 基线构建说明（仅作来源追溯）

> 本文件随 v1.8.0 冻结源码保留，不是 v1.9.0 的构建入口。当前版本请以
> `README_BUILD.md` 为准；其默认引擎、Tagged PDF 与发布验收流程已升级。

本源码包包含五册、合并总册、公共样式、绘图源、构建入口、自动检查代码与测试代码。所有路径均相对于解压后的源码包根目录。

## 构建环境

- Windows PowerShell 5.1 或 PowerShell 7
- TeX Live 2026
- XeLaTeX
- latexmk 4.88
- 讲义所用中文与数学字体可由 TeX 环境正常找到

## 构建命令

在源码包根目录依次执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target merged_full -OutputDir build-output\merged_full
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target volume1 -OutputDir build-output\volume1
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target volume2 -OutputDir build-output\volume2
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target volume3 -OutputDir build-output\volume3
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target volume4 -OutputDir build-output\volume4
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target volume5 -OutputDir build-output\volume5
```

为避免 TeX 缓存与索引工具互相干扰，六个目标应串行构建。合并完整解析版入口为 `讲义源码/合并总册/main_full.tex`，五册入口分别是五个分册目录中的 `main.tex`。

## 自动检查

```powershell
python -m unittest discover -s tests -v
python qa\static_source_audit.py
python qa\link_and_label_audit.py
```

发布候选的完整 G1/G2/G3 证据不在源码 ZIP 内重复存放，可在同级发布目录的 `qa` 文件夹查看。
