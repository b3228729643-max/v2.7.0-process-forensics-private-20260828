# 分册入口 tagged-PDF 兼容修复：主线 L1 验收

- 时间：`2026-08-24T23:45:53+08:00`
- 主线提交：`49b7622`
- 触发请求：B-EXM-P02 `SR-B-P02-001`
- 最终结论：`PASS_L1_VOLUME1`

## 根因

- 5 个独立分册 `main.tex` 仍在 `\documentclass` 前启用实验性 `\DocumentMetadata{tagging=on,...}`。
- 当前安装的 tagged-PDF block 层会在章节地图延迟渲染时抢先解释 `itemize[leftmargin=...]` 的 enumitem 键，并报 `Package block Error: Some keys specified on the itemize environment are unknown`。
- 合并总册入口已经显式禁用该实验层并通过完整 R99/R7 构建，因此问题不是 enumitem 缺失，也不是章节内容错误，而是独立分册入口未同步既定兼容策略。

## 修复范围

- 只修改 5 个独立分册 `main.tex`：移除实验性 `\DocumentMetadata` 调用，保留 `\SLSetBookMetadata`/hyperref 的标准 PDF 元数据路径，并写明与合并总册相同的兼容原因。
- 在 `src/tests/test_layout_source_contracts.py` 增加聚焦契约：必须恰有 5 个分册入口，均不得重新启用 `\DocumentMetadata`，且仍须加载统一文档类、公共样式和 `\SLSetBookMetadata`。
- 未修改章节正文、图源、公共样式、索引、manifest 或 B/A 工作树。

## 已执行验证

- `python -m unittest src.tests.test_layout_source_contracts`
- 结果：5 tests，`OK`。
- `git diff --check`：PASS。

## L1 TeX 冒烟验证

- B-P03 归还受控排版时隙并确认 TeX 进程为零后，主线构建 volume1：
  `powershell -ExecutionPolicy Bypass -File .\src\build.ps1 -Target volume1 -Engine lualatex -OutputDir ...\src\build\volume1_r136_entry_smoke`
- wrapper/child exit 0；输出 191 页 A4，1,420,375 bytes，PDF 1.7、无加密、无旋转。
- `Package block Error`、LaTeX hard error、fatal/emergency/capacity/memory/no-output 及 over/underfull hbox/vbox 全部为0。
- 原失败点在首章 `dependencybox` 结束；构建完整越过11章并自然收敛，问题不再出现。
- 独立分册仍有6条指向其他分册的未定义引用警告；这是不包含其他分册标签的既有范围特性，不属于本次block兼容错误，且build wrapper按既定门返回PASS。
- 主线打开150dpi物理页7--8：章节地图、学习目标列表、依赖路线与后续正文无裁切、重叠、缺失或异常分页。
- 终态 latexmk/lualatex/luatex/luahbtex 均为NONE；受控排版时隙已释放。
