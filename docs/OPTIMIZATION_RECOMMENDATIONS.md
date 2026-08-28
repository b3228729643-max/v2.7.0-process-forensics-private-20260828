# 优化建议

目标不是降低质量，而是把验证成本与实际变更风险对齐。

## P0：立即实施

### 1. 将一次性 controller/auditor 改为版本化、测试过的公共工具

不要为每个 UID 重新生成数百行 PowerShell。建立一套参数化工具：

- `build_controller.ps1`
- `seal_evidence.ps1`
- `audit_evidence.ps1`
- `manifest_tool.py`

对它们做固定单元测试与集成测试；UID 任务只提交 JSON 参数。这样可以消除 `.Count`、alias、OrderedDictionary、String.Replace 等重复脚本错误。

### 2. 正式调用前增加 disposable dry-run

在空临时目录运行完整控制逻辑，但不触碰正式根。dry-run 必须覆盖：

- 0/1/N 行集合；
- 0/1/N 个 `=`；
- 路径 canonicalization；
- OrderedDictionary/PSCustomObject 两种行类型；
- 文件和目录 ReadOnly；
- marker 生成与解析；
- snapshot；
- language mode。

正式 invocation=1 可以保留，但必须在同代码、同运行时的 dry-run 通过后才消费。

### 3. 用增量影响集替代每轮全量 `C(N,2)`

保存稳定 object registry。若只修改对象 `x`，只重新裁决：

- `x` 与其几何邻域对象；
- 受遮罩/路径影响的对象；
- 全局语义和页面门。

未受影响 pair 通过上一候选的 `(source object hash, geometry hash, render transform hash)` 继承。只有影响集不确定时才回退到全量 pairs。

### 4. 缓存去重并禁止把 TeX cache 复制进 evidence root

把 TEXMF cache 放在按 engine/font/input hash 寻址的共享只读目录。证据根只记录：

- cache key；
- toolchain identity；
- 构建命令；
- 输入/输出 hash。

不复制 `luatex-cache`、`.lua`、`.luc`。预计可直接消除约 6 GB 重复数据。

### 5. 明确“业务 PASS”和“控制封存 PASS”两个状态机

业务证据闭合后形成不可变 content bundle。控制失败只能改变 `control_status`，不能迫使业务视图/N/C/manual 重新生成。control reseal 直接引用 content bundle 的 Merkle root，不再复制全部 material。

## P1：本轮项目内实施

### 6. 风险分层的 Main 验收

Main 应复核：

- 变更源；
- hard defect ROI；
- manifest 根 hash；
- 角色隔离与关键控制。

低风险机械字段由经过测试的 auditor 输出签名报告，Main 不再逐文件重复扫描。可保留随机抽样和失败时全量复核。

### 7. 让 fresh 角色独立判断，但允许复用不可争议输入索引

独立性不等于必须重复 OCR/page localization。可以提供只读、候选绑定的：

- PDF page map；
- source-label-caption map；
- object registry 形式定义。

角色仍独立做视觉/数学裁决，但不用重复寻找同一页和重新发明 ID。

### 8. 把 checkpoint 合并为事件日志

中央状态只在以下事件更新：

- role start；
- substantive verdict；
- source change；
- build result；
- final acceptance/blocker。

自然进度写入 append-only NDJSON 事件流，不必每次重写多份大 Markdown 状态文件。

### 9. 构建槽允许“预检失败不计正式调用”

只有 engine child 真正启动后才消费 build invocation。root 创建、路径参数、cache 可写性、source identity 等 controller 前置错误，应归类为 preflight，允许修正后再进入唯一正式 build。

### 10. 统一 seal schema

固定一份 JSON Schema / CSV schema / marker schema，不再由每个任务手写 13、18、22、25、28、30、33 行 marker。建议 marker 只包含：

- schema version；
- content Merkle root；
- manifest SHA；
- role/verdict；
- controller/auditor tool version；
- timestamps；
- post-write count。

其他字段放入 `SEAL_AUDIT.json`，避免重复绑定和拼接错误。

## P2：下一版本架构

### 11. 内容寻址证据库

以 SHA-256 保存唯一 blob，evidence root 只存 manifests/links。重复 PNG、PDF、font cache 只落一次。用 SQLite/Parquet 保存 object/pair 账，不为每轮复制 CSV。

### 12. 将几何审查自动化为候选生成 + 人工例外确认

自动计算 visible-ink masks、connected components、clearance、clip 与 endpoint topology。人工只审：

- overlap 候选；
- 小于阈值的近邻；
- 语义/数学；
- 代表性全图。

不要人工逐行确认 1,770 个明显分离 pair。

### 13. 建立失败分类与自动回归库

把本项目已出现的控制错误全部做成 regression tests。至少覆盖：

- scalar `.Count`；
- OrderedDictionary property access；
- `New-Item -LiteralPath`；
- DirectoryInfo ReadOnly；
- aliases；
- operator precedence；
- String.Replace overload；
- dot-source language mode；
- multiline marker。

### 14. 设立流程预算

每个 UID 预设：

- 最大 build 次数；
- 最大 full-pair 次数；
- 最大 control reseal 次数；
- 证据体积预算；
- checkpoint 数量预算。

超过预算自动触发流程复盘，而不是继续复制同一模式。

## 建议的精简工作流

```text
source patch
  -> shared preflight/tool tests
  -> one controlled build
  -> machine candidate extraction
  -> human review of candidates + semantics + representative full page
  -> immutable content bundle / Merkle root
  -> standard seal tool
  -> independent risk-based acceptance
  -> commit / next role
```

## 预期收益

保守估计：

- 缓存去重：减少 50% 以上磁盘体积；
- 增量 pair 审查：局部修订轮减少 80%–98% pair 人工量；
- 公共 seal 工具：基本消除因脚本拼写/StrictMode 造成的 control reseal；
- 事件日志与风险分层：显著减少中央协调回合与上下文膨胀。

