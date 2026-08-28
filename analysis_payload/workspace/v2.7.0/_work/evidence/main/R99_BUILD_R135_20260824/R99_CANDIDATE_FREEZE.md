# R99 官方候选冻结记录

- 冻结时间：2026-08-24T22:52:00+08:00
- 主线提交：`b09f12302a75c417a4df50c0547c73ebdeb80900`
- 集成内容：Dialogue A `FIG-P608-01` SA2 单文件修复提交 `e933f09e757d406954edd09f8ce0a326248c7da9`
- 官方候选：`R99`
- PDF：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r99_fullbook\main_full.pdf`
- 物理页数：`814`
- 字节数：`4,940,207`
- SHA-256：`E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6`

## 构建判定

- `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r99_fullbook -NoPublish` 最终退出码：`0`。
- 首次全量轮因并发排版导致系统内存耗尽；保留且核验 UTF-8 辅助文件后，同一输出目录强制依赖收敛成功，未清理或从零重建。
- `symbols.idx`：355 entries accepted，0 rejected，0 warnings。
- `main_full.idx`：731 entries accepted，0 rejected，0 warnings。
- 最终 `main_full.log` 硬诊断计数：0（LaTeX/Package error、undefined、duplicate、overfull/underfull、fatal、emergency、memory exhausted）。
- PDF：814/814 页 A4、无旋转；14 组字体全部嵌入且含 Unicode 映射。
- 导航审计：PASS；5 册、37 章、双索引、273 bookmarks、4,952 internal links、7,419 named destinations、无无效书签/链接、无意外版本字符串。
- 主线工作树在候选冻结时干净。

## 边界

R99 是供 `FIG-P608-01` 全新独立 SA1 与随后隔离 SA3 使用的官方候选；本记录不等于 P608 `A_LOCAL_PASS`，也不等于 99 图或全书最终 PASS。
