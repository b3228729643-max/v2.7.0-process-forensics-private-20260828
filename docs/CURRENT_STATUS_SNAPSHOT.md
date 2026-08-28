# 归档时状态快照

## 中央已登记状态

- 中央 revision：550
- Main branch：`v2.7.0/integration`
- Main HEAD：`f1874b2a4f1ffe823968d417019cfdc2c5641888`
- 官方候选：R116，817 页
- 官方 PDF：4,967,281 bytes
- SHA-256：`19F3D0413AD8C72B4D855B2C23246F10DD7ACECF2FD1E984AEE9F25E1051D3DC`
- inventory：`30 SA1 / 30 SA2 / 0 SA3 / 40 local pass`
- B 内容线：66/66
- 严格最终：0/99

## 中央 revision 550 后、归档过程中到达但尚未写回中央 inventory 的事实

### P690 / C 支线

- fresh R116 SA2 已返回 sealed PASS 方向。
- 独立定位 physical 740 / printed 727 / Fig35.6。
- N=28，C=378；objects/pairs/glyph/math/geometry/semantic/ROI/page 全部完成。
- hard/clip/illegal overlap/unresolved 为 0。
- token：`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`。
- 控制披露：sealed audit 未单独测量 ADS，因此仍需 Main 独立判定。

### P126 / A 支线

- R116 fresh SA1 已确认两处 text–curve visible-ink collision，并回 SA2。
- 当前 source 静态补丁为 4,809 bytes/SHA `4CE06E3B00402A6C14774CC95D86348D4056B493C030CADDB9BB53DC53C6AAC2`。
- 原 R19 control root 因 marker move 后 Snapshot 运行时错误被拒收。
- R19A V1 static 脚本被 Main 在 invocation0/0 静态拒收。
- R19A V2 controller/auditor 已冻结并通过第一轮静态身份/AST/absence 检查，但在用户切换到归档任务时尚未获正式执行授权。

## 本快照的含义

本仓库记录的是“为什么耗时”和“过程如何演化”，并不是最终发布包。网页端模型应区分：

- 已被 Main 接受的事实；
- 支线 sealed 但尚待 Main 独立接受的事实；
- STATIC_ONLY、未构建或未封存的方向；
- 被控制缺口拒收但业务内容仍有参考价值的根。

