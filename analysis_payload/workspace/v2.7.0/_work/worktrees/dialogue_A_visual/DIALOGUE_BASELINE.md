# v2.7.0 双支线共同基线

- 建立时间：2026-08-24（Asia/Shanghai）
- 主对话：`v2.7.0主线`
- 第一分对话：`v2.7.0支线1`（对话 A / 视觉域）
- 第二分对话：`v2.7.0支线2`（对话 B / 内容与数学域）
- 恢复入口：`v2.7.0/_work/state/v2.7.0续_交接文档.md` 第 14 节 Revision 130
- Goal SHA-256：`4FB8A2B615AC7EDA635D0F8DACACE9CF88692153A049D4A04BE06B56BCB53F1A`
- 官方候选：R98，813 页，4,934,249 bytes
- R98 SHA-256：`52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41`
- 集成分支：`v2.7.0/integration`
- 视觉分支：`v2.7.0/dialogue-a-visual`
- 内容分支：`v2.7.0/dialogue-b-content`

生成物目录 `build/` 与 `src/build/` 不进入基线提交；两支线以集成树中的 R98 为只读权威候选，并在各自工作树生成本地构建产物。Revision 130 已保留的证据目录不删除、不从零重建。
