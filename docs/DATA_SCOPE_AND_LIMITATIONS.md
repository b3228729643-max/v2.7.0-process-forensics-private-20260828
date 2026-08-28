# 数据范围与限制

## 已直接进入普通 Git 的内容

- 模型可读的 Markdown、JSON、CSV、TSV、PowerShell、Python、TeX、日志、patch/diff、marker 等。
- Goal 执行包的 11 个原始输入/说明文件。
- 当前关键 P126/P690 视觉证据和官方 R116 PDF。
- 全部原始路径级 inventory。
- Git 历史 bundle。

## 使用 Git LFS 的内容

- `full_archive/v2.7.0-full-workspace-20260828.tar.zst.part-001`
- `full_archive/v2.7.0-full-workspace-20260828.tar.zst.part-002`
- `full_archive/v2.7.0-full-workspace-20260828.tar.zst.part-003`
- `full_archive/v2.7.0-full-workspace-20260828.tar.zst.part-004`
- `full_archive/FULL_ARCHIVE_PARTS.csv`
- `full_archive/FULL_ARCHIVE_SUMMARY.json`

四个 LFS 分卷按序拼接后恢复 `v2.7.0-full-workspace-20260828.tar.zst`。该归档保存原始 v2.7.0 工作区全内容，包括普通 Git 不适合承载的大量 PNG、PDF、Lua/LUC cache 和重复生成物。完整归档为 4,939,633,376 bytes、211,202 个 tar 条目，SHA-256 为 `2B97102D44F9229D253A546C78E2B08E4312E9F27DA7B08EFD3F9E94C68AE027`。

## 为什么需要分层

原始工作区约 11.14 GB；普通 GitHub blob 单文件受限，且 159,150 张 PNG 与 6 GB 以上 Lua/LUC cache 会使网页搜索和模型分析几乎不可用。正文包服务于网页分析，全量压缩包服务于取证完整性。

## 敏感信息

已扫描常见 GitHub PAT、私钥、API key、client secret 和 password 赋值模式；候选文件数为 0。该扫描不构成对任意隐写或未知格式秘密的绝对保证，因此仓库必须保持 private。

## 时间一致性

本归档生成期间支线仍可能返回新 handoff。`docs/CURRENT_STATUS_SNAPSHOT.md` 明确记录了中央 revision 550 与归档中后到事实的区别。
