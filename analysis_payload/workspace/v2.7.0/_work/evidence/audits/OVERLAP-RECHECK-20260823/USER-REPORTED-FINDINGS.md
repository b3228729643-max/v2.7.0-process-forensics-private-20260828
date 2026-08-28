# 用户放大证据触发的视觉验收纠正

本文件只记录用户在 300 dpi 最终候选放大图中直接指出的几何叠压。旧机器门、旧根 PASS 和旧独立 PASS 均不能覆盖这些新视觉证据。

## FIG-P632-01｜R3.4｜FAIL

- 用户截图：`C:\Users\ASUS\AppData\Local\Temp\codex-clipboard-f0694e9e-2852-4a9f-9375-2041a5c7a189.png`。
- 对应最终证据：`evidence/figures/FIG-P632-01/R3/p632_root_r3p4_standalone_300dpi.png`；同构问题亦见彩色页和灰度页。
- 缺陷：上下两个条件面板的 `\int_{\mathbb R}` 大积分号及其下限与各自左纵轴占用同一 x 位置，字形与轴线混成一笔。
- 处置：撤回 R3.4 根视觉 PASS；中止 SA1/SA3 R3.4；中央状态退回 `根视觉返修`；R2.3 已仅将两个公式块右移，等待 R3.5 重建验证。

## FIG-P580-01｜R3.1｜FAIL

- 用户截图：`C:\Users\ASUS\AppData\Local\Temp\codex-clipboard-f46bcb2c-6b84-4cd9-bdfa-f6685dc6b449.png`。
- 对应接受证据：`evidence/figures/FIG-P580-01/R3/p580_root_r3p1_standalone_300dpi.png`，并须在最终彩色/灰度页复核。
- 缺陷：右图比率说明框没有容纳第二行公式；`w(1)=0.96` 一端向左溢出并侵入纵轴与 `0.4` 刻度区，`w(4)=0.96` 一端向右溢出框体。
- 当前官方 R94 的同 UID 还存在另一项独立缺陷：左面板先绘制的 `虚线 q_L(x)=2/5` 被后绘制的不透明白底“点线：支撑边界 / x=5/2”覆盖；`=2` 完全消失并留下孤立的 `5`/残片。这是可见文字遮挡与语义完整性 FAIL，不能因 `OVERLAP_PIXEL_COUNT` 在最终合成图上被白底抹成 0 而通过。必须保存 source→pre-occlusion→opaque-background→final-visible 绘制顺序证据。
- 处置：撤回 P580 中央 `通过`；数学复算仍保留为有效，但 numeric verification 标记为视觉返修待定；纳入 28 图全量只读回溯审计。

## 统一后续门

- 独立语义对象在 300 dpi 原图上须有明确可见白隙；任何线穿入字形外接框、与上下限连笔、公式溢框或文字侵入轴/曲线/刻度均 FAIL。
- `full_page_200dpi`、彩色 `figure_crop_300dpi`、`standalone_300dpi`、`grayscale_300dpi` 任一失败则对象失败；证据缺失、掩膜污染、映射未知或净空无法确认均直接 FAIL，不得进入 SA3。
