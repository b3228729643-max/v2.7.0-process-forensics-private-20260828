# FIG-P580-01｜ROOT-APPLY-R3.1

## 结论

- PASS_LOCAL_PENDING_INDEPENDENT
- SPLIT_REQUIRED=NO
- R3 首版两份 PDF 与机器门通过，但三张 300 dpi 视图均显示中心方形点穿透三行比率卡并遮住 `$5/2$`，且卡片压住目标曲线峰部，故根线程明确判视觉失败并保留全部 R3 工件。R2.1 将比率卡固定到 `y\in[0.345,0.455]` 两行区域；R3.1 的源码、机器门与三视图通过。

## 对象与身份

- canonical UID：FIG-P580-01
- legacy ID：FIG-V5-C02-07
- label：fig:V5-C02-is-support
- 唯一图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_is_support.tex`
- 单图约束：figure=1、tikzpicture=1、caption=1、label=1、combined alt=1；不拆图。
- 页级定位：图31.6，页579。
- Goal 附录 B44 与旧中央清单的状态机结论属于相邻 P578 串项，已按 D-012 固化为只读冲突证据。

## 解析密度与比率证书

- 共同定义域为 `[0,5]`。`p(x)=6x(5-x)/125` 非负，解析积分为1；`q_L=(2/5)1_[0,5/2]` 与 `q_R=1/5` 的解析积分也均为1。
- 左图 `(5/2,5)` 上 `q_L=0<p`，故 `p` 不绝对连续于 `q_L`；该缺失区目标质量由对称性或直接积分得到 `1/2`。
- 右图 `q_R>0` 于全域，故 `p\ll q_R`。`w=p/q_R=6x(5-x)/25`，在 `x=1,5/2,4` 依次为 `24/25=0.96`、`3/2=1.50`、`24/25=0.96`。
- 三个曲线点与三个显示比率均从同一 `slpivtarget`/`ISQRHeight` 公式链派生；没有硬编码曲线端点，也没有用曲线竖直距离表示比率。

## 字号、版式与图文链

- 普通文字、刻度、轴标签和比率卡均至少9.6pt，标题10.2pt；源码无低于9.6pt声明，无 `scale`、`xscale`、`yscale`、`resizebox`、`scalebox` 或 `transform shape`。
- 左图以目标实线、提议虚线、支撑边界点线、缺失区斜线纹理和端点形状表达支持不足；右图以实线/虚线及圆/方/三角点表达覆盖和三个比率，灰度不依赖颜色。
- R3.1 比率卡底边高于中心方点上缘约4.6mm；三点、目标峰、卡片边框与两行文字均完整可见。
- 正文和 page wrapper 在输入前给出三条固定密度与观察任务，输入后依次为 `\FloatBarrier` 与专属读图检查；题注只保留一条支持结论，并明确支持覆盖不等于低方差或可靠性。

## R3.1 构建与机器门

- page：`p580_root_r3p1_page.pdf`，69,295 bytes，A4 单页。
- standalone：`p580_root_r3p1_standalone.pdf`，42,370 bytes，A4 单页。
- AUX：`fig:V5-C02-is-support = 31.6 / page 579`。
- 两份最终日志对致命错误、未定义引用、重复标签、Overfull/Underfull 和缺字硬模式命中均为0。
- page 7个字体、standalone 5个字体，全部嵌入、子集化并带 Unicode 映射。
- 两份 FLS 均命中 v2.7.0 wrapper、`release_version.tex`、公共图样式与当前唯一图源。
- source JSON 为9图且P580唯一；numeric manifest 为37条且身份唯一；中央 CSV 为99行×19列、99个唯一 UID 且P580唯一。

## R3.1 三视图

- `p580_root_r3p1_page_300dpi.png`
- `p580_root_r3p1_gray_page_300dpi.png`
- `p580_root_r3p1_standalone_300dpi.png`

三图均为2481×3508、300 dpi。根线程逐图实看：共同域、三条密度、左支持边界/零基线/纹理区、右三点与两行比率卡、题注和图后检查均清楚；无碰撞、裁切、串字或灰度失辨。

## 根级裁决

根级局部验收通过，中央清单暂记“待独立复核”。只有新的隔离 SA1 与独立 SA3 均判 `PASS / SPLIT_REQUIRED=NO / NEW_ISSUE=NONE` 后，才可写最终接受报告并冻结本图。
