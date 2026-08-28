# 《统计学习方法初学者讲义》v2.7.0 源码说明

本源码包可在 Windows PowerShell 中离线重建五册合并总册。正式且唯一的整书入口是：

```text
src\讲义源码\合并总册\main_full.tex
```

发布版本由 `manifests\release_version.tex` 中的 `\SLReleaseVersion` 唯一定义；LaTeX 封面、页眉、PDF 元数据、内部完整解析版链接和根构建脚本均从该变量派生。

## 构建环境

- Windows PowerShell 5.1 或更高版本；
- TeX Live 2026 或功能等价发行版；
- LuaLaTeX、`latexmk`、`makeindex`；
- 西文正文依次回退 `STIX Two Text`、`Libertinus Serif`、`TeX Gyre Termes`；数学字体依次回退 `STIX Two Math`、`Libertinus Math`、`TeX Gyre Termes Math`；
- 无衬线字体使用 TeX Live 自带的 `TeX Gyre Heros`；中文字体依次回退 Noto Serif/Sans SC、Source Han Serif/Sans SC、Fandol；
- 构建不需要网络，也不会自动安装或分发软件、宏包或字体。

## 一键干净构建

在解压后的 `v2.7.0` 目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build_v2.7.0.ps1 -Engine lualatex -Clean
```

成功后生成：

```text
统计学习方法初学者讲义_合并总册v2.7.0_完整解析版.pdf
```

若只需验收、不发布顶层 PDF，可增加 `-NoPublish`。如构建被外部时限中断，确认没有残留 TeX 进程且源码未变后，可改用 `-Resume` 续跑。查看解析后的构建计划而不写产物：

```powershell
powershell -ExecutionPolicy Bypass -File .\build_v2.7.0.ps1 -DryRun
```

## 对象与源码结构

- `src\讲义源码`：五册共 37 章及合并入口，覆盖 66 道正文例题、596 个知识点、192 个定义/定理类对象、59 组核心推导和 553 道章末练习；
- `src\绘图源码`：99 幅带编号正式图的源文件，另有封面与阅读路线所用的 2 幅未编号辅助插图；
- `styles\figure-style-v2.3.1.tex`：稳定的公共绘图 API；文件名保留 API 世代号，不是当前讲义发布号；
- `manifests`：发布版本、逐图源映射与实施说明；
- `scripts`：源码包结构验证与辅助审计脚本。

旧说明中的“101 幅图”把 99 幅带编号正式图与 `UFIG-P001-01`、`UFIG-P158-01` 两幅未编号辅助插图合并计数；v2.7.0 的逐图任务以索引中的 99 幅正式图为准，两幅辅助插图仍在全书逐页视觉审查中核对。`BND-P015-01` 是表格/文本框版面边界对象，从未计入正式绘图数。

源码包不包含构建缓存、预览图、执行状态目录、Git 元数据或生成 PDF。
