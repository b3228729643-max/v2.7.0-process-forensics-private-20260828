# R350 P067 静态补丁接受与唯一 direct build 授权

时间：2026-08-27T14:31:02+08:00

## 主线独立复核

- 输入源：`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`，R111基准3866 bytes，SHA-256 `03372740AB8015EFFB7BC6CFBBDC669A1E8FBF52246291491B1B0C506513B864`。
- 主线从基准文本在内存中执行回传的两个唯一替换，两个旧片段计数均恰1；按原LF/UTF-8-no-BOM重构得到4015 bytes、SHA-256 `C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0`，与A回传after identity一致。
- 差异只增加`yticklabels={0,0.15,,0.35}`以抑制自动0.30标签，并在同一0.30 tick坐标以原文本`0.3`、原8.6/10.3pt字号、局部`xshift=-2pt,yshift=-4.5pt`重放。0.35自动tick/label、0.30 tick、四个PMF概率、CDF levels、轴/面板/端点/题注/颜色/线型与其余几何不变。
- 静态预测新0.30标签对0.35约2.0 native-300dpi px、对0.15约2.5px；该值只用于授权构建，不构成视觉PASS。

## 静态根控制面

- root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R2_SA2_STATIC_TICK_LABEL_PATCH_R111_20260827`。
- payload5、ordinary7；7/7文件与root只读；manifest↔FS path/bytes/SHA/NTFS ticks mismatch0；WSTOP唯一严格最后，主线复算margin589,462,304 ticks、at-or-after0。
- report SHA-256 `3CB0CF223B0DEE7D961D8A77BEAB2793C6F8F45A07D2D0C2E48CE6AB954729CA`，handoff SHA-256 `F8211495100769DFA62A350222B498E209DD168208396A22D0B51D3B00922519`，均只读且与回传一致。

## 唯一构建槽

- 授权HANDOFF_ID：`A-R111-P067-SA2-DIRECT-BUILD-R3-20260827`。
- 唯一新根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R3_SA2_TICK_LABEL_PATCH_R111_DIRECT_BUILD_20260827`；授权时file/dir均不存在。
- 授权前主线独立检查`latexmk/lualatex/luatex/luahbtex`进程为0。
- 只允许一个PowerShell7 controller、一个direct LuaLaTeX child、invocation1、retry0、latexmk0、无并发/自动重试/中止；`TEXMFVAR/TEXMFCACHE/TEXMFCONFIG`全部绑定新根独立`texcache`。
- 构建前后必须复核source=`C570597B...FFA0`与固定standalone wrapper身份不变；自然exit后PDF恰1，并报告路径/bytes/SHA、controller/child PID、起止时间、exit/natural/interrupted、终态四类TeX进程0，然后立即释放槽。
- 槽释放后仅从新PDF执行非TeX全量对象/all-pairs、`.35/.30/.15`原生1x/8x净距、PMF/CDF数学、灰度、题注和页面回归及真实人工账；通过前不得commit，不得启动fresh role、第二UID或中央写入。

## 并行只读角色

P660 R111 fresh SA1保持同一实例/root。主线只读旁证已见44/44对象、41/41关键关系与数学/题注/上下文人工记录落盘且当前hard方向0；尚无manifest/WSTOP，不提前计PASS或迁移角色。
