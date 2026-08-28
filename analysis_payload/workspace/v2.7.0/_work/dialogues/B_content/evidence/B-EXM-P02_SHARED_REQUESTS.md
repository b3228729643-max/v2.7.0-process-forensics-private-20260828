# B-EXM-P02 共享请求

## SR-B-P02-001：独立分册构建入口的 block/itemize 键错误

- owner_requested: main/shared build writer
- B action: 只登记，不修改构建入口、共享宏或样式
- observed_on: volume1、volume3、volume4、volume5
- command_shape: `src/build.ps1 -Target volumeN -Engine lualatex -OutputDir ...`
- exit_code: 12（四册一致）
- error: `Package block Error: Some keys specified on the itemize environment are unknown.`
- first_locations: `V1-C01.tex:33`、`V3-C01.tex:57`、`V4-C01.tex:72`、`V5-C01.tex:64`
- P02 relation: 四处均不在本批 5 个修改文件/例题块内；P01 合并总册构建曾成功，故按共享分册入口问题路由。
- evidence: 工作树 `build/dialogue_B_content/B-EXM-P02/volumeN/qa`
- requested_follow_up: 主线在不阻塞 P02 内容集成的前提下，检查各分册入口加载 block/itemize 键的顺序或选项；B 不越权修复。

P02 改动另用已成功合并本缓存的 `-Resume` 增量合并构建验证。
