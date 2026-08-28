# R530 V3 静态通过与唯一执行授权

- 时间：2026-08-28T15:25:16+08:00
- inventory：`30 SA1 / 30 SA2 / 1 SA3 / 39 local pass`；严格最终0/99；B 66/66。

## 静态验收

- Controller：20,415 bytes，SHA-256=`3FEED0680C9756B87275344CACBDF8D8FE048816A9DC00003382E85F340E0125`，ReadOnly，AST0，sole Move1。
- Auditor：21,300 bytes，SHA-256=`96E6818AB86BAB9C31A50A569736BE3F323BE8AC87226AC5504EBA7DB9FFFD74`，ReadOnly，AST0，Move0。
- Destination、V3 stage、controller result、auditor result在授权时均absent；invocation0/0。

Main复核完整V2→V3 diff：controller仅V3 identity/schema/stage/result变化；auditor同类变化加唯一实质修复，`marker_lines`与`marker_keys`由已验证的`$markerLines.Count`和`$markerMap.Count`派生。V3无stale literal26语义。StrictMode内存marker/parser/result测试为28/28/28/28。

V2已全文验证的copy137→payload139/controls3/final142、规范路径与五字段、source/destination files+child dirs+root ADS Stop门、full-tree ReadOnly、root-external future ReadOnly marker sole-final Move、old-root before/after0、postmarker0、dynamic CSV/JSON、cache-pyc/reparse合同均未改变。

## 执行边界

1. 冻结controller只可invocation1/retry0；首错停止。
2. 仅controller natural exit0且result success=true，并且HANDOFF/operation/controller identity/invocation/retry精确时，冻结auditor可invocation1/retry0；首错停止。
3. 任一失败均不得编辑、重试、清理、续封、替换或调用剩余步骤。
4. 双成功只回sealed control结果；不得重读或重跑业务PDF/render/N/C/pair/manual/math/semantic，不得source/TeX/build/Git/central/role动作。

P126保持SA2等待Main独立root验收；P689同一fresh SA3继续且未计local pass。
