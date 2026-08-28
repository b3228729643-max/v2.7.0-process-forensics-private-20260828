# v2.7.0 执行过程取证与耗时复盘

这是一个**私有分析仓库**，用于让 GitHub 网页端的高能力模型审阅《统计学习方法讲义》v2.7.0 项目的完整执行过程，回答两个问题：

1. 为什么任务耗时远超预期？
2. 在不降低最终质量的前提下，流程、协议、工具和任务拆分应如何优化？

## 建议从这里开始

1. 阅读 [`docs/WHY_THIS_TOOK_SO_LONG.md`](docs/WHY_THIS_TOOK_SO_LONG.md)。
2. 阅读 [`docs/OPTIMIZATION_RECOMMENDATIONS.md`](docs/OPTIMIZATION_RECOMMENDATIONS.md)。
3. 将 [`docs/PRO_MODEL_ANALYSIS_PROMPT.md`](docs/PRO_MODEL_ANALYSIS_PROMPT.md) 作为网页端模型的首条提示词。
4. 用 [`docs/CURRENT_STATUS_SNAPSHOT.md`](docs/CURRENT_STATUS_SNAPSHOT.md) 了解归档时的实时状态。
5. 需要追溯事实时，优先查看：
   - `analysis_payload/workspace/runtime_context/`
   - `analysis_payload/workspace/v2.7.0/_work/state/`
   - `analysis_payload/workspace/v2.7.0/_work/evidence/main/`
   - `analysis_payload/workspace/v2.7.0/_work/handoff/`
   - `analysis_payload/workspace/v2.7.0/_work/dialogues/`
   - `inventory/FULL_WORKSPACE_FILE_INVENTORY.csv`

## 归档范围

- 原始 v2.7.0 工作区：185,757 个文件，约 11.14 GB。
- 网页分析正文包：18,372 个模型可读的源码、状态、报告、账本、脚本和日志，约 1.01 GB。
- 关键视觉证据：128 个文件，约 11 MB。
- 完整路径级清单：覆盖全部原始文件，包含路径、大小、时间、扩展名、是否进入正文包及排除原因。
- 本地 Git 历史：通过 `project-history.bundle` 保存全部本地分支和提交。
- 全量原始内容：4.60 GiB 的压缩归档拆为 4 个分卷，放入 `full_archive/` 并使用 Git LFS 管理；重组后的 SHA-256 为 `2B97102D44F9229D253A546C78E2B08E4312E9F27DA7B08EFD3F9E94C68AE027`。

## 重要说明

- 本仓库的“正文包”有意排除了大量重复生成的 TeX/Lua 字体缓存、`.luc`、大批渲染 PNG/PDF 等。它们不是被遗忘，而是由完整清单和全量压缩归档覆盖。
- 这类二进制/缓存材料不适合直接作为普通 Git blob：原工作区中 `.lua` 约 3.65 GB、`.luc` 约 2.37 GB、PNG 约 3.18 GB。
- `selected_visual_evidence/` 保留了当前关键 P126/P690 视觉证据，便于网页端直接抽查。
- 归档是过程取证快照，不代表项目已经最终完成。归档时严格最终通过仍为 0/99。

## 仓库结构

```text
docs/                       耗时分析、优化建议、时间线、模型提示词
inventory/                  全量文件清单与体积统计
analysis_payload/           可直接供模型搜索和阅读的过程/源码正文
selected_visual_evidence/   当前关键视觉证据与官方 R116 PDF
full_archive/               全量压缩归档分卷、逐卷哈希和重组说明（Git LFS）
tools/                      构建本归档的可复现脚本
project-history.bundle      全部本地 Git 分支历史
```

## 恢复全量归档

先按 `full_archive/FULL_ARCHIVE_PARTS.csv` 核对 4 个分卷的大小与 SHA-256，再按文件名顺序拼接：

```powershell
cmd /c copy /b full_archive\v2.7.0-full-workspace-20260828.tar.zst.part-001+full_archive\v2.7.0-full-workspace-20260828.tar.zst.part-002+full_archive\v2.7.0-full-workspace-20260828.tar.zst.part-003+full_archive\v2.7.0-full-workspace-20260828.tar.zst.part-004 full_archive\v2.7.0-full-workspace-20260828.tar.zst
```

重组文件应为 4,939,633,376 bytes，且 SHA-256 应与上述值一致。随后可用 `tar -tf` 校验并用 `tar -xf` 解包。

## 数据安全

归档前对常见 GitHub PAT、私钥、API key、client secret、password 赋值模式进行了路径级扫描，候选文件数为 0。仓库必须保持 private；不要改为 public。
