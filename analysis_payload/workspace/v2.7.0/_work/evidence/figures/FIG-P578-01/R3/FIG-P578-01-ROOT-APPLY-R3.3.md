# FIG-P578-01｜ROOT-APPLY-R3.3

## 结论

- PASS_LOCAL_PENDING_INDEPENDENT
- SPLIT_REQUIRED=NO
- R3 首次构建因自定义 TikZ 样式名 `step` 与预置键冲突而失败；R3.1 虽生成单页，但有两处 Overfull 和两组出口卡重叠；R3.2 技术门通过但均匀源“失败”标签压住状态名。三版失败历史均保留。R3.3 的源码、机器门和三视图通过。

## 对象与身份

- canonical UID：FIG-P578-01
- legacy ID：FIG-V5-C02-06
- label：fig:V5-C02-rejection-flow
- 唯一图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_flow.tex`
- 单图约束：figure=1、tikzpicture=1、caption=1、label=1、combined alt=1；不拆图。
- 页级定位：图31.5，物理页577。

## 状态机语义

- 随机调用前验证 `N,B`、`c`、密度有限非负、支持覆盖、有限比率及全局 `p\le cq`；随后初始化 `m=a=0` 与空前缀。
- 两级短路固定先判 `a=N`、再判 `m=B`：`N=0`（含 `N=B=0`）零随机调用返回 `completed`，`N>0,B=0` 返回 `budget_stop`；同轮目标与预算同时命中时 `completed` 优先。
- 提议源成功后才令 `m\leftarrow m+1`；只有 `U\le\rho` 的接受分支原子追加 `Y` 并增加 `a`，普通拒绝不追加。
- 提议源、均匀源、密度/比率和包络失败均保留最后合法 `X_{1:a},m,a` 及失败位置。流程只使用正式状态词表中适用的五项；包络越界为 `invalid_input`，`envelope_condition_failure` 只作诊断。
- 图、正文、wrapper、source JSON 与中央清单统一使用 `m,a,N,B` 和 `\mathrm U(0,1)`。

## 字号、布局与图文链

- 普通节点和边标签均为9.6pt/11.6pt；无低于9.6pt字号声明，无 `scale`、`scalebox` 或 `resizebox` 整体缩放。
- 主链为实线箭头；成功为圆角框、预算为虚线椭圆、异常为双线框、普通拒绝为虚线框，灰度不依赖颜色。
- 七个右侧出口错开排列，边标签与卡片均有净空；左回路、两级优先级说明和底部合流完全位于版心内，未碰 caption。
- 正文链为首次引用与工程说明、单独页图、`\FloatBarrier`、专属读图检查；题注只保留需要区分的四类结局。
- Goal 附录 B43 与旧中央清单的包络几何结论属于相邻 P577 对象错位，已按 D-011 保留冲突证据；Goal 输入未修改。

## R3.3 构建与机器门

- page：`p578_root_r3p3_page.pdf`，73,438 bytes，A4单页。
- standalone：`p578_root_r3p3_standalone.pdf`，59,369 bytes，A4单页。
- AUX：`fig:V5-C02-rejection-flow = 31.5 / page 577`。
- 两份最终日志对致命错误、未定义引用、重复标签、Overfull/Underfull 和缺字硬模式命中均为0。
- page 7个字体、standalone 5个字体，全部嵌入、子集化并带Unicode映射。
- 两份 FLS 均命中 v2.7.0 wrapper、`release_version.tex` 与当前唯一图源。
- source JSON 为9图且P578唯一；中央 CSV 为99行×19列、99个唯一UID且P578唯一。

## R3.3 三视图

- `p578_root_r3p3_page_300dpi.png`
- `p578_root_r3p3_gray_page_300dpi.png`
- `p578_root_r3p3_standalone_300dpi.png`

三图均为2481×3508、300dpi。根线程逐图实看：预检、零调用短路、`m/a`更新、五类状态出口、失败位置、完成优先级、接受/普通拒绝、回路、题注和读图检查均清楚；无碰撞、裁切、串字或灰度失辨。

## 根级裁决

根级局部验收通过，中央清单暂记“待独立复核”。只有新的隔离 SA1 与独立 SA3 均判 `PASS / SPLIT_REQUIRED=NO / NEW_ISSUE=NONE` 后，才可写最终接受报告并冻结本图。
