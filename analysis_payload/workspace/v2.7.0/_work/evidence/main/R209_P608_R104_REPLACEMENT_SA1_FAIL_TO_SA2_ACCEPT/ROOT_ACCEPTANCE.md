# R209｜FIG-P608-01 R104 fresh replacement SA1 中央接受

- 中央裁决：`ACCEPT_FAIL_TO_SA2`
- HANDOFF_ID：`A-R104-P608-SA1-FRESH-REPLACEMENT-20260826`
- 官方候选：R104，物理页 661（印刷页 648，图 32.8）
- 证据根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R10_SA1_FRESH_REPLACEMENT_R104_20260826`
- P608 当前单源 SHA-256：`78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`

## 接受结论

R10 replacement SA1 修复了 R9 的人工观察时间完整性缺口。四份人工账均满足逐行 `opened_at <= observed_at <= decided_at <= ledger mtime < WSTOP mtime`，时间失败为 0；人工账计数为 68 glyph、60 graphic、12 critical pair、16 view。

从零分母为 N=128（68 glyph + 60 graphic，含 6 个 MATH_RULE），全部无序 pair 为 8,128/8,128。运行均值 15/15 复算通过，`t=20` 为 2.0000；字体像素微差依 R168 仅作 advisory。

两处真实几何硬失败经主线打开 native 1x 与 nearest 8x 证据确认：

1. `PAIR-06596`：上面板首个 marker 与独立 y-axis 真实重叠并遮挡轴线；
2. `PAIR-06650`：同一 marker 与 y-arrowhead 基部真实接触合并。

这两项属于 R168 仍保留的真实非法几何重叠，不是字体阈值或 taxonomy 微差。`PAIR-06428` 的 aggregate mask purity 问题只说明该证据不能用于清除失败，不覆盖上述硬失败。

因此 FIG-P608-01 从 SA1 迁移至 SA2；不得启动 SA3，不计 A_LOCAL_PASS。下一步只允许单一 P608 图源的窄几何修复静态阶段，保持数据值、运行均值、标签、题注和其余语义不变；未获中央构建槽前禁止 TeX。

## 中央机械复核

- manifest 声明/行数/实际 payload：265/265/265；ordinary=267；
- duplicate、missing、extra、bytes、SHA mismatch：均 0；
- manifest SHA-256：`0CA3A8BFE555592A806B469581D108E9BF5AA4BDCC74F89BE3134725717FA68C`，与 WSTOP 声明一致；
- manual time failure：0；
- 267/267 文件只读；非默认 ADS=0；
- WSTOP 严格最新：`2026-08-25T19:21:31.1272813Z`，前一最新文件为 manifest `2026-08-25T19:21:08.1750791Z`；
- TeX、源码修改、提交、SA3：均为 0。

## Inventory 迁移

- 迁移前：`35 SA1 / 52 SA2 / 0 SA3 / 12 A_LOCAL_PASS`
- 迁移后：`34 SA1 / 53 SA2 / 0 SA3 / 12 A_LOCAL_PASS`
- 全书严格最终：仍为 `0/99`

