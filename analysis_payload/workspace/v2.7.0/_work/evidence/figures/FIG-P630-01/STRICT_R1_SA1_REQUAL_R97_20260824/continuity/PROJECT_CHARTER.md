---
task_id: FIG-P630-01-SA1-REQUAL-R97
charter_revision: 1
created_at: 2026-08-24T17:56:28+08:00
updated_at: 2026-08-24T17:56:28+08:00
---

# 最终目标

作为全新隔离 SA1，对 FIG-P630-01（图33.1）在 R97 官方候选上做只读重新资格审查，独立重建严格视觉、字体、字形、路径、全 pair、数学语义和页面融合证据，并返回唯一允许的 SA1 终态。

# 最终交付物

- 本目录内的官方候选身份与定位记录、原生渲染、逐字形和逐路径原始掩膜、1×/8×人工核验材料、全对象/全 pair ledger、逐门报告、manifest、MANIFEST 与最终 RESULT。
- 最后写入 `WRITE_STOPPED`，之后不得再写。

# 权威输入

- `D:\Users\ASUS\.codex\attachments\e9427863-0663-4847-93b3-d9c784a212b5\pasted-text.txt`
- 项目 `AGENTS.md`
- `STRICT_FIGURE_EVIDENCE_SCHEMA.md`
- `STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md`
- 第33章直接正文 `V5-C04.tex`
- 当前图源 `fig_v5_c04_dependency_graph.tex`
- 官方候选 `strict_current_r97_fullbook/main_full.pdf`，预期 SHA256 `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`、813页。

# 工作目录与输出目录

唯一可写根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P630-01\STRICT_R1_SA1_REQUAL_R97_20260824`。

# 硬性约束

- 只读审查，不改业务源码、公共样式、正文、中央状态、库存、官方构建或其他证据。
- 不读取、搜索、列举或继承任何既有 FIG-P630-01 evidence、旧 PASS、库存结论或其他代理判断。
- 物理页、印刷页、图号与严格图框须由 aux/fls/正文/PDF 自行定位。
- 300dpi 原生坐标、20/255 阈值、逐字形唯一 raw mask、逐路径唯一前景对象、100% contact、C(N,2) 全 pair 和全部硬门均按更严格协议执行。
- 任一硬门 FAIL 不能由其他 PASS 抵消。

# 禁止事项

- 禁止从零重建项目、远程推送、安装软件/宏包/字体、破坏性 Git 操作。
- 禁止脚本批量伪写人工 PASS；所有人工 ledger 必须在实际打开对应证据后逐项填写。
- 禁止把 UID 当页码、把旧证据或局部构建冒充官方候选。

# 明确排除内容

- 其他 UID、其他图、其他代理目录和任何中央发布/状态写入。
- 本 SA1 不做源码修复，不宣布最终关闭。

# 验收标准

- 身份、页码与图框闭合；四视图存在并实际打开。
- 100% reader-visible glyph 与全部可见 drawing/path 有唯一对象、非空纯净 mask、1×/8×人工记录。
- N 对象对应恰好 C(N,2) 个无序 pair；0 漏对象、0 漏 pair、零未决人工状态、0 非默认 ADS。
- 字号、H_INK、D/E、重叠、裁切、净空、数学语义、灰度与页面融合逐门一致。
- manifest 引用全部存在，临时零字节清除；`WRITE_STOPPED` 最后写且之后零写入。

# 指令优先级

1. 系统和安全规则
2. 用户当前明确要求
3. 有效项目规则
4. 用户提供的权威实施材料
5. Skill 默认策略

# 安全边界

- 不记录密码、API Key、令牌或其他秘密。
