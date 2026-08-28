# FIG-P632-01｜ROOT APPLY R3.4

RESULT: **FAIL_SUPERSEDED_BY_USER_VISUAL_EVIDENCE**  
SPLIT_REQUIRED: **NO**

> **撤回说明（2026-08-23）：** 用户放大截图确认两块条件面板的积分号及下限与左纵轴重叠。根线程撤回先前视觉 PASS；R3.4 仅保留为失败证据，不得用于独立终审或发布。

## 已否决候选

- UID：`FIG-P632-01`；旧 ID：`FIG-V5-C04-02`。
- 图号/逻辑页：图 33.2 / 664；AUX 精确回写 `{{33.2}{664}...}`。
- 页面 PDF：`p632_root_r3p4_page.pdf`，A4 单页，82151 bytes。
- 独立 PDF：`p632_root_r3p4_standalone.pdf`，A4 单页，50291 bytes。
- 300 dpi 证据：彩色页 739195 bytes、灰度页 703154 bytes、独立图 303332 bytes；三者均为 2481×3508。
- 构建管线：TeX Live 2026 LuaLaTeX；MiKTeX 未使用。

## 失败链保留

- R3：源宏含数字，被 TeX 分词为 `\sl` 后终止；两份日志均为 `No pages of output`。
- R3.1/R3.2：误用 XeLaTeX 后由 `xdvipdfmx` 对可变字体报错；无 PDF，不作为图源失败。
- R3.3：LuaLaTeX 机器门通过，但根级三图视觉检查发现左轴/公式、上下条件面板、峰位标记与警示框碰撞，判 FAIL。
- R2.1 将 39 个唯一宏字母化；R2.2 仅调整局部坐标与映射路径；R3.4 因用户视觉证据否决，后续须由 R2.3/R3.5 替代。

## 数学与元数据

- 同一模型使用 `rho=3/5`、`a=1`、`b=4/5`、协方差 `[[1,3/5],[3/5,1]]`。
- 联合密度为 `5/(8*pi) exp[-25/32 (x1^2-(6/5)x1*x2+x2^2)]`；特征值 `8/5` 与 `2/5`，主轴 45°。
- `X1|X2=4/5 ~ N(12/25,16/25)`；`X2|X1=1 ~ N(3/5,16/25)`；共同峰值 `5/(4sqrt(2*pi))`。
- `m2(4/5)=0.28969155276148273`；`m1(1)=0.24197072451914337`；两条条件密度全实线积分为 1。
- 零边缘处只声明预先指定的可测正则条件版本，且仅在边缘几乎处处意义下唯一；本高斯例不触发该边界。
- wrapper、章节首引/专属读图句、source JSON 与 numeric manifest 已同步 v2.7.0 / canonical UID；numeric manifest 保持 37/37 唯一对象。

## R3.4 机器门

- page/standalone 硬日志命中：0/0。
- 两份 PDF 均为 A4 单页；页面版 8 种、独立版 4 种字体全部 `emb=yes sub=yes uni=yes`。
- FLS 均命中当前 wrapper、`statlearnbook.sty`、`release_version.tex`、`figure-style-v2.3.1.tex` 与当前 P632 图源。
- 静态契约：单 figure、单 TikZ、单 caption/label/combined alt；全局可见节点 9.6pt；无总体缩放；旧含数字控制序列 0。

## R3.4 根级视觉门（已纠正）

- 彩色页面：**FAIL**。图 33.2 虽位于首引后且题注/专属读图句同页，但两个条件面板的 `\int_{\mathbb R}` 积分号及下限与各自左纵轴占用同一位置。
- 灰度页面：**FAIL**。同一叠压在去色后更明显，不能以线型仍可辨替代几何净空要求。
- 独立图：**FAIL**。用户放大截图明确显示下方面板积分号/下限与纵轴混成一条线；上方面板为同构布局，须一并修复。
- SA1/SA3 R3.4 终审已中止；中央状态已退回 `根视觉返修`。

RESULT=FAIL_SUPERSEDED_BY_USER_VISUAL_EVIDENCE  
SPLIT_REQUIRED=NO
