# R367 P067 R112 fresh SA3 FAIL 验收与最窄静态源码授权

时间：2026-08-27T16:48:09+08:00

## sealed FAIL 独立验收

- HANDOFF_ID：`A-R112-P067-SA3-FRESH-ISOLATED-20260827`；actual instance：`/root/p067_r112_fresh_sa3`；sealed root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R5_SA3_FRESH_ISOLATED_R112_20260827`。
- fresh SA3独立定位R112 physical69，冻结`N130=95 text+35 graphic`、`C8385`；manual objects130/130、all-pair reconciliation8385/8385、views6/6；413/413 PNG可打开。
- 唯一真实hard defect为`GFX-007`：CDF step path整体提前一个支撑区间。当前图将累计值0.15画在`0.5<=t<1`、0.45画在`1<=t<2`，而`x=1`端点同时表达open0/closed0.15，后续跳点同样错一段；这违反右连续、PMF到CDF的累积关系和题注语义。
- 主线实际打开full page、native figure crop、standalone、grayscale、graphic sheet02及GFX-007 nearest8x，独立确认平台段与open/filled endpoints的相对位置确有上述错位；无tofu、错码、不可读、明显失衡、clip或final-visible illegal overlap反证，字体微栅格仅R168 advisory。
- 当前source中CDF line为`\addplot[const plot mark right,...]`，随后坐标固定为`{(.5,0) (1,.15) (2,.45) (3,.80) (4,1) (4.5,1)}`，filled endpoints固定为`(1,.15)...(4,1)`，open endpoints固定为`(1,0)...(4,.80)`。本地PGF手册确认`const plot mark left`是左连续段handler别名，`const plot mark right`把mark放在右端；因此当前handler正是错位机制。
- 正式接受`SA3_FAIL_RETURN_TO_SA2`；不得计A_LOCAL/global/final PASS，不得派SA3。P067由SA3返回SA2。

## 封存与身份复核

- payload433、7,931,532 bytes；ordinary435；435/435文件与7/7目录含root ReadOnly。
- canonical aggregate以forward relative path、TAB、bytes、TAB、uppercase SHA、CRLF重算为`6EDBDA8129271189E20A50B221B4C44506E662790C60C177D9A08D291CD5657C`，与SEAL一致。
- WSTOP唯一严格最新，margin316,123,303 ticks；at-or-after excluding marker0、postmarker0；ADS/cache-pyc/reparse0。
- SEAL SHA=`5F0335B6E3F320549FE25168E08B9E03A1B545D60E95C422901E4573519B989C`；WSTOP SHA=`9C687B87FB14F0AED8B6BADDF7340FD9080A9740DC0B7BDAEF9D517121E0D217`。
- report SHA=`127A0A33FD18B320C6DD34362D11C49B102A55374E46408D41D20DF858CE0D9F`；handoff SHA=`98CFF15CB5BF7AD91CD6E2AC427A36A3E219CFEB2241C17F3D00DEE026D4953A`。sealed root/report/handoff永久冻结。

## 唯一最窄 static-only source scope

- 授权HANDOFF_ID：`A-R112-P067-SA2-STATIC-CDF-STEP-HANDLER-20260827`。
- 唯一source：`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`；before必须保持4,015 bytes/SHA=`C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0`。
- 唯一允许的源码变化：把CDF曲线的handler token `const plot mark right`改为`const plot mark left`。
- 必须保持坐标列表、四个filled endpoints、四个open endpoints、PMF数据、R111已集成的PMF tick-label补丁、axes、fonts、colors、strokes、annotations、caption及其他全部token不变；预期Git精确1 file/1 insertion/1 deletion、index empty、`git diff --check` PASS。
- 静态报告必须逐区间证明新handler给出`[0.5,1):0`、`[1,2):0.15`、`[2,3):0.45`、`[3,4):0.80`、`[4,4.5]:1`，并说明与既有open/filled endpoints、PMF累计及右连续一致；同时列出唯一潜在回归为step path与guide/labels/axes/markers的像素关系，必须由新PDF全图重测。
- 新static evidence root必须启动前不存在，单次封存、全文件/目录/root ReadOnly、WSTOP绝对最后、postmarker0，根外只读审计。当前仅授权static source edit/evidence；禁止TeX/build、commit、fresh role、第二source/UID或central state写。完成后只可请求显式唯一controlled standalone/direct LuaLaTeX build slot。

## P662 并行边界

- P662原SA1内容方向仍保留，但原根因malformed WSTOP key values冻结拒收；R366授权的唯一evidence-only sibling control reseal正在同一C链执行。
- 未收到并独立验收reseal前不得派P662 fresh SA3；P067 static链与P662 reseal不得互相读写或管理。

inventory更新为`32 SA1 / 38 SA2 / 0 SA3 / 29 local pass`；main HEAD仍为`27fca4d1a0c9034807a161c1bffa4f4d8f099339`且clean，R112仍为唯一正式候选，TeX0。
