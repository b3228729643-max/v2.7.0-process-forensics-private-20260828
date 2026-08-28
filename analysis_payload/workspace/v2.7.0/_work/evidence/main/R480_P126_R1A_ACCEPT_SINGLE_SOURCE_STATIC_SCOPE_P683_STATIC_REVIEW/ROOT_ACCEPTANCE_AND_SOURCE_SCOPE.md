# R480 P126 R1A接受与唯一单源static scope

时间：2026-08-28T07:56:35+08:00

## R1A接受

Main独立接受P126 R1A evidence-only control reseal。固定HANDOFF=`A-R115-P126-SA2-R168-READONLY-CONTROL-RESEAL-V1-20260828`；controller与auditor各唯一invocation1/retry0/natural exit0，冻结身份未变。

独立复算：57 files、5 dirs含root全ReadOnly；COPY_IDENTITY52、PAYLOAD_MANIFEST54，copy source/destination与manifest/FS的relative path、bytes、SHA256、CreationTimeUtc ticks、LastWriteTimeUtc ticks mismatch0，canonical ordinary set diff0。WSTOP25行、bad/duplicate0，COPY_IDENTITY/COPY_PROVENANCE/PAYLOAD_MANIFEST/SEAL_AUDIT SHA绑定全精确；marker含root strict latest margin5,999,607,739 ticks、at-or-after0。JSON/CSV parse、ADS、cache-pyc、reparse均0。

Main按冻结算法复算destination snapshot=`839C5438C2EB538A133A56704BD31B68946280D712C32FC5478B5964E8153379`，old R1 snapshot=`436F4108CB92A2EC2719BAB141786C49A8703066253C003CEFC56D654D036B14`，均与controller/auditor回报精确一致。root-external result/audit/report/handoff的bytes/SHA/ReadOnly也精确。

## 唯一source scope

P126保持SA2。仅授权修改：

`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C08/fig_v1_c08_coordinate.tex`

before=4,093 bytes，SHA-256=`328A61A7C16DC11546BA165D698A22E1431B1B6AA3C04B16A4C40B52E4F3673C`。

静态补丁必须作为一个统一数学修复：

1. 四层等高线来自同一个正定二次型，且其主轴明确不与`x_1/x_2`坐标轴对齐；不得只做互不一致的视觉旋转。
2. `q0`至`q7`仍为交替竖直/水平的单坐标更新；每一步都必须是该二次型在固定另一坐标时的精确坐标最小值。静态证据写出Hessian/正定性、每步更新后对应偏导为0及目标函数严格或非增下降；`x^*`保持真实最优点，最终点只能表达逼近，不能伪称有限步必达。
3. 消除已确认四项native实墨关系：T01 `x_1`↔contour19px、T04 step1↔contour6px、T05 step2↔contour4px、T08 step5↔horizontal axis22px。优先通过一致几何与局部数字anchor/xshift/yshift解决；禁止用opaque fill遮掉冲突作为替代。
4. 两个legend swatch必须在灰度中稳定呈现solid与多段dash区别；可缩短dash周期或调整局部legend sample，但保持更新`x_1/x_2`文字和对应轨迹角色。

允许的附带改动仅限必要的axis limits、contour参数、q坐标、数字node anchor/xshift/yshift、legend dash/sample参数。不得改图中/题注/alt文字、font declarations、axis names、figure label、颜色角色、共享宏、章节、构建入口或其他源。

## 当前权限

A仅可生成并封存static evidence，回唯一diff、数学证明、预测清空间距与`STATIC_ONLY_NOT_RENDERED_NOT_PASS`。未授权TeX/build、commit、fresh role、第二UID或central写。Main接受static patch后才可能另授唯一controlled direct build slot。

C/P683仅维持R478的静态脚本暂停，等待Main逐文件审查。inventory保持`32 SA1 / 31 SA2 / 0 SA3 / 37 local pass`，严格最终0/99。
