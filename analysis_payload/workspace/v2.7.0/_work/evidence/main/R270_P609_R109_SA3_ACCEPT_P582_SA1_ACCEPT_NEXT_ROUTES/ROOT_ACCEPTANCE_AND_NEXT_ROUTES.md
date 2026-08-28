# Revision 270 — P609 SA3 接受、P582 SA1 接受与下一并行路由

时间：2026-08-26T23:12:23+08:00  
主线：`v2.7.0/integration` / `59e7afd81ba3171ab9de5c90ed589fed3424155e`（clean）  
官方候选：R109，817 页，4,967,054 bytes，SHA-256 `936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9`

## P609 root acceptance

- 接受唯一有效 replacement：`C-FIG-P609-01-R109-SA3-FRESH-ISOLATED-REPLACEMENT-V2`。
- 原 V1 隔离暴露根永久保持 `UNSEALED_ISOLATION_COMPROMISED`，未读取、未续写、未用于裁决。
- replacement 从零闭合 `N=32`、`C=496`，人工对象 `32/32`、人工 pair `496/496`；一般可见最小字号 9.6pt，57/57 像素硬门通过，非法重叠、裁切、真实硬失败均为 0，最小净距 7px。
- 主线只读复算：ordinary=35，manifest payload=33；文件缺失/多余/bytes/SHA mismatch=0；35/35 文件只读，root ReadOnly；`WRITE_STOPPED` 严格晚于其他文件 355,565,861 ticks，postmarker=0。
- 主线实际打开 `figure_caption_crop_300dpi.png`、`semantic_object_overlay_300dpi.png` 与 `roi_right_panel_nearest8x.png`；ACF、K=6 截断、有限样本 ESS、题注与版面均无反证。
- 正式裁决：`FIG-P609-01 = C_LOCAL_PASS`。冻结当前源码、R109 证据、SA1/SA3 角色、report/handoff；禁止重复角色或为本 UID 再启 TeX。

## P582 SA1 acceptance

- 接受 `A-R109-P582-SA1-FRESH-ISOLATED-20260826` 的 SA1 PASS；它不等于 A_LOCAL_PASS。
- 最终可见分母 `N=105`（78 glyph + 27 graphic），`C=5,460`；被后绘制 marker 完全遮蔽的 source stem G016 在人工账前有理排除并全量重算。
- 人工 glyph 78/78、graphic 27/27、critical 20/20 PASS；overlap/clip/真实硬失败均 0。5 个微像素字号标记与 `.380` 箭头 1px 白隙按 R168 仅作 advisory。
- 主线只读复核：386/386 文件只读；`WRITE_STOPPED` 严格晚于其他文件 10,219,936 ticks；manifest/FS identity、ADS/cache/pyc/reparse/postmarker 均通过。sealed helper 的 CSV/JSON 原始类型比较误报已披露，归一化外部审计通过，未改 sealed root。
- 主线实际打开官方图裁图与 `P3464_quad_8x_nearest.png`；曲线、数值、箭头、公式、题注清楚，1px 白隙可见，无反证。
- 正式裁决：P582 保持 SA1，授权另一个 `fork_turns=none`、全新根的 R109 fresh isolated SA3；禁止读取本 SA1/任何旧 P582 证据、代理状态或旧结论，禁止 TeX/源码写/提交/第二角色。

## 加速路由

- C 支线已释放 P609，立即授权 B58 / `FIG-P630-01` 做 R109 `READONLY_R168_ADJUDICATION_FIRST`。
- 当前唯一源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_dependency_graph.tex`，2,342 bytes，SHA-256 `746163570B90750C1BE9731029C450B2F800D43296075FC22D71B9D9F72F2E43`。
- 旧失败仅涉及 U+2212/U+22C5 低轮廓像素高度；按 R168 先从 R109 原生 1x/8x 只读判断。若无缺字/tofu/错码、真实不可读、明显失衡、裁切、非法重叠或语义错误，直接封 `NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`；不得因微像素高度或 taxonomy 单独返源。
- 若确认真实硬缺陷，只回报最窄单源 static scope，不自行改源或启 TeX。禁止第二 UID/第二角色。

## Inventory

在两个新 actual identity 回传前：`32 SA1 / 47 SA2 / 0 SA3 / 20 local pass`；严格最终仍为 `0/99`，B 例题链保持 `66/66`。
