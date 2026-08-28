---
task_id: C-FIG-P667-01-R114-SA3-FRESH-ISOLATED-V1
charter_revision: 1
created_at: 2026-08-27T23:47:34.3078106+08:00
updated_at: 2026-08-27T23:47:34.3078106+08:00
---

# 最终目标

对当前官方 R114 中 UID FIG-P667-01 完成一次全新、隔离、只读源码的 SA3 独立盲审，并只封存一个 PASS 或 FAIL 结果。

# 最终交付物

 assigned evidence root 内的机器证据、逐 ID 人工观察台账、报告、handoff、材料身份、manifest，以及唯一严格最新的 WRITE_STOPPED。

# 权威输入

- official R114 PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf`
- current FIG-P667-01 source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_conjugate_update.tex`
- `D:\Users\ASUS\Desktop\机器学习\GOAL.md` and its directly referenced strict pixel protocol/evidence schema
- only genuinely necessary current V5-C05 prose

# 工作目录与输出目录

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P667-01\sa3_r114_fresh_isolated_v1`

# 硬性约束

- 固定 HANDOFF_ID 和实例身份。
- 输入只读；无构建槽；不运行 TeX/LuaLaTeX/latexmk。
- 从 R114 独立定位图与题注，冻结完整读者可见对象分母和全部无序对。
- 阈值只作建议；R168 规定的真实可见失败才可硬 FAIL。
- WRITE_STOPPED 作为唯一最后根内容操作，之后仅做根外只读审计。

# 禁止事项

不得读取任何 SA1、SA2、先前 P667/其他 UID 证据或结论；不得读中央状态/清单/历史/Git 历史；不得写源码、构建、Git 或共享状态；不得管理外部 TeX 进程。

# 明确排除内容

第二 UID、第二 P667 角色、源码修订、重编译、全书状态判定、C_LOCAL/global/final pass 计数。

# 验收标准

生成要求的可复核证据并实际打开全部决定性视图；人工台账必须是观察后逐 ID 撰写；封存后 manifest/FS 身份、ReadOnly、WRITE_STOPPED 时序和 hygiene 全部通过根外只读终审。

# 指令优先级

1. 系统和安全规则
2. 用户当前明确要求
3. 有效项目规则
4. 用户提供的权威实施材料
5. Skill 默认策略

# 安全边界

- 不记录密码、API Key、令牌或其他秘密。
