# Revision 223｜P640 R105 fresh SA1 硬几何失败接受并回SA2

- 时间：`2026-08-26T07:03:04+08:00`
- UID：`FIG-P640-01`
- HANDOFF_ID：`MAIN-R105-P640-SA1-FRESH-ISOLATED-REPLACEMENT-20260826`
- 官方候选：R105物理页690，PDF SHA-256 `F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1`。

## 接受的失败事实

- 分母：253个前景对象（242 glyph + 11 semantic path groups）；全部unordered pairs `31,878/31,878`。
- `.99` open marker与专用竖tick已经修复：raw-mask交集0，连续矢量边界正空隙0.2137756pt（300dpi约0.8907317px），不是接触。
- 唯一硬失败：右图金色ESS曲线与极限注释第二行`N_eff/N→0`的首个`N`发生真实可见融合；ID=`GLYPH-0109` ↔ `PATH-RIGHT-ESS-CURVE`。
- 主线独立打开native1x与8x ROI，确认曲线切入`N`左下笔画/衬线；这是真实几何非法重叠，R168不放宽。
- clip0；页面融合、灰度、数学语义、题注文字及R168字体可读性其余PASS。

## 封存披露

- preseal manifest 314行，主线逐文件path/bytes/SHA 0 mismatch；preseal actual314，ordinary317，317/317只读，ADS0；report/handoff只读。
- 控制层存在一个诚实缺口：`seal/closure.json`的mtime晚于`seal/WSTOP`约5ms，因此WSTOP不是绝对最后文件。该根不得作为完整PASS封存包或复用为后续PASS证据，保持只读。
- 本轮只接受主线已独立视觉确认的`FAIL_TO_SA2`方向；无需为已坐实硬失败重做evidence reseal。

## SA2 范围

- P640由SA1迁回SA2。
- 仅授权C在唯一源`V5-C04/fig_v5_c04_mixing_rho_comparison.tex`做static-only最窄修复：优先给第47--48行两行极限注释节点加入真实源码级白色不透明背景（如`fill=white,inner sep=1pt`），或等价地局部重定位；不得改曲线、数据、公式、字体、`.99` marker/tick关系、坐标轴、caption或其他源。
- 静态冻结后只请求唯一构建槽；未授权前禁TeX、提交和fresh角色。

## 中央状态

- inventory=`33 SA1 / 53 SA2 / 1 SA3 / 12 A_LOCAL_PASS`；严格最终`0/99`。
