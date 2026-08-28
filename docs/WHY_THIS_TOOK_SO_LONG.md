# 为什么这个任务耗时如此之长

结论先行：主要耗时并不是 LaTeX 源码本身复杂，而是执行协议把每个局部视觉修复扩张成了一个高成本、不可复用、失败后不能原地续跑的取证流程。质量要求合理，但验证粒度、隔离策略、控制封存与人工全配对审查叠加后，产生了明显的乘法效应。

## 量化事实

| 指标 | 归档时数值 | 说明 |
|---|---:|---|
| 原始工作区文件 | 185,757 | 大量证据、渲染图、缓存和重复控制根 |
| 原始工作区体积 | 11.14 GB | 其中大部分不是最终源码 |
| 中央状态修订 | 550 | 表明协调/复核/路由频率极高 |
| `STRICT_*` 目录 | 318 | 每轮或每个控制链通常建立独立不可变根 |
| control-reseal 目录 | 58 | 很多业务证据已完成，只因封存控制缺口而复制重封 |
| direct-build 目录 | 39 | 单构建槽、一次调用、失败即停造成大量离散构建根 |
| controller 脚本 | 59 | 多为一次性冻结脚本 |
| auditor 脚本 | 54 | 常与 controller 独立运行 |
| stop/seal markers | 187 | ReadOnly、未来 FILETIME、严格最新等封存协议 |
| manifests | 1,307 | 身份、复制、payload、preseal 等多层清单 |
| reports / handoffs | 616 / 219 | 过程报告远多于最终成果 |
| PNG | 159,150 / 3.18 GB | 大量 native、grayscale、overlay、ROI、NN8x |
| Lua + LUC 缓存 | 6.02 GB | 重复 TeX 字体缓存，是最大体积来源 |

## 核心原因一：验证成本呈平方增长

视觉角色经常将 N 个 reader-visible objects 的**所有无序对**全部列举并人工裁决，成本为 `C(N,2)`。

典型例子：

- N=60 时，pair ledger 为 1,770 行。
- N=38 时，pair ledger 为 703 行。
- 同一 P126 图在多轮修订后反复重新生成 N/C、打开 ROI、逐对象和逐 pair 写账。

局部修改一个标签坐标，理论上只影响少量邻域关系；当前协议却常要求重新审查全部 1,770 对。修订轮数增加时，总成本近似 `修订次数 × N²`。

## 核心原因二：fresh-isolated 角色禁止复用稳定事实

SA1、SA2、SA3 被要求：

- 使用不同实例和新证据根；
- 不读取旧角色的页号、N/C、pair、像素或结论；
- 独立重新定位页面、冻结 denominator、生成视图并写人工账。

这提高了独立性，但也让“已被多个角色稳定确认的非受影响区域”无法复用。即使源文件只改一处，后续 fresh 角色仍从零重新完成整图审查。

## 核心原因三：封存控制比业务判断更易失败

大量失败并非视觉或数学失败，而是一次性 PowerShell 控制脚本的小型运行时问题，例如：

- `New-Item -LiteralPath` 参数不存在；
- StrictMode 下标量没有 `.Count`；
- `Group-Object` 无法按 OrderedDictionary 的伪属性分组；
- DirectoryInfo 没有可写 `IsReadOnly` 属性；
- String.Replace 误绑定 char overload；
- `R` helper 名称被 PowerShell alias 抢占；
- 数组加法与 pipeline precedence 触发 `DirectoryInfo.op_Addition`；
- dot-source 跨 language mode 失败；
- marker 字符串拼接或换行生成非法 KEY=VALUE。

协议又规定 controller invocation=1、retry=0、首错即停、不得原地修补。于是一个业务已闭合的根，会因为控制脚本一行错误而进入：

1. 现场冻结；
2. Main 独立裁决；
3. 新建 sibling evidence-only control reseal；
4. 新 controller/auditor 静态审查；
5. 再复制全部 material、重建 manifest、重设 ReadOnly、重新移动 marker；
6. Main 再次独立验收。

58 个 control-reseal 目录正是这种流程放大的直接迹象。

## 核心原因四：过度细化的“唯一调用/唯一构建槽”

构建被拆成严格的一次性槽：controller 一次、direct LuaLaTeX child 一次、retry=0、version probe=0、second invocation=0。一次环境错误或 controller 前置错误就会产生一个完整失败根，并需要 Main 重新授权新的 sibling build。

这避免了隐藏重试，但把本可在预检阶段发现的问题推迟到昂贵的正式调用中。

## 核心原因五：证据与缓存没有去重

体积最大的材料是重复生成物：

- `.lua` 约 3.65 GB；
- `.luc` 约 2.37 GB；
- PNG 约 3.18 GB。

同一字体缓存文件在多个 evidence root 中重复出现，单个常达约 28 MB。每个新 build/reseal root复制缓存与证据，导致磁盘遍历、hash、ReadOnly、manifest 与审计时间同步增长。

相比之下，主 Git 仓库的 loose objects 只有约 17 MB；说明主要膨胀来自过程证据，不是源码历史。

## 核心原因六：Main 的独立复核重复了支线机械工作

支线会计算：

- bytes/SHA/FILETIME；
- manifest set；
- ReadOnly；
- marker schema；
- strict-latest / at-or-after；
- ADS/cache/reparse；
- pair/object ledger。

Main 为了“独立接受”又重复计算同一批门。双重验证能降低伪阳性，但当前几乎没有按风险分层，低风险字段也被反复全量复核。

## 核心原因七：状态记录过密

中央状态达到 revision 550。大量自然 checkpoint、静态准备、preinvoke、执行结果、control reseal、handoff 都会触发中央文档更新。状态足够可追溯，但协调写入本身成为显著工作负载，并进一步扩大上下文。

## 核心原因八：任务尚未完成，且质量门是 99 图全覆盖

归档时中央 inventory 为：

- 30 SA1
- 30 SA2
- 0 SA3
- 40 local pass
- 严格最终 0/99
- B 内容线 66/66

因此“耗时很长”不只是过去阶段缓慢，也因为目标本身仍要求 99 个图的严格闭环，而视觉线尚有大量 SA1/SA2/SA3 迁移和最终验收。

## 根本判断

当前体系优化的是“每一步都能法证式证明”，而不是“以最少计算得到同等可靠结论”。它把罕见的控制风险当成每一步的默认风险，并把所有局部变化当成整图变化。最终表现为：

```text
局部源码变化
  × fresh 角色数
  × 全对象/全配对人工审查
  × controller/auditor 双控制
  × Main 再复核
  × 失败后不可续跑的新 sibling 根
```

这就是主要的乘法耗时来源。

