# Codex 运行环境

- 桌面应用包：`OpenAI.Codex_26.803.10989.0_x64__2p2nqsd0c76g0`（从已安装 WindowsApps 路径读取）。
- `codex.exe`：路径可定位，但 WindowsApps ACL 在当前 shell 中拒绝直接执行；不能据此伪造 CLI 版本或 `/hooks` 结果。
- 本地 Hook schema 证据：用户级 `D:\Users\ASUS\.codex\hooks.json` 已使用 `PreCompact` 与 `SessionStart` 的嵌套 `hooks` 结构；项目配置据此适配。
- 项目级 Hook：`PreCompact` 与 `SessionStart` 脚本语法检查和 `dry_run` 均通过；当前桌面应用是否加载/信任项目 Hook 仍由运行时决定，不能由 shell 假装确认。
- Python：`py -3` = Python 3.9.12。
- 工作区依赖包：Codex primary runtime bundle `26.805.11740`。
- 模型标识：当前桌面线程未暴露可可靠写入构建说明的精确模型标识，不估算。
- `model_auto_compact_token_limit` / `model_auto_compact_token_limit_scope`：本地项目与用户配置未发现显式值，保留运行时默认值。
- 网络：构建不依赖网络；不自动安装软件、宏包或字体。
