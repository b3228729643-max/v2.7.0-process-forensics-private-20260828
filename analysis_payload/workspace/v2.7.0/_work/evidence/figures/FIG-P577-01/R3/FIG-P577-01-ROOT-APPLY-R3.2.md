# FIG-P577-01｜ROOT-APPLY-R3.2

## 结论

- PASS_LOCAL_PENDING_INDEPENDENT
- SPLIT_REQUIRED=NO
- R3 首次构建因摘要卡换行误写为展示数学起始符而失败；R3.1 编译成功但有 2.65746pt Overfull 且摘要卡遮挡曲线、直接标签与最小差箭头。两版均只保留为失败历史。R3.2 的源码、机器门和三视图均通过。

## 对象与身份

- canonical UID：FIG-P577-01
- legacy ID：FIG-V5-C02-05
- label：fig:V5-C02-rejection-envelope
- 唯一图源：src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_envelope.tex
- 单图约束：figure=1、tikzpicture=1、axis=1、caption=1、label=1、实际 combined alt=1，无拆图。
- 页级定位：图 31.4，物理页 576。

## 数学与教学语义

- 目标密度 p(y)=6y(1-y)，提议密度 q(y)=1，支撑集为 [0,1]，合法包络常数 c=8/5=1.6。
- p 在 y=1/2 取最大值 3/2，因此 min(cq-p)=1/10；接受率为 1/c=5/8，每个接受值的平均提议数为 c=8/5，拒绝区面积为 c-1=3/5。
- 接受点 y=1/4、h=4/5 给出 U=1/2<=45/64；拒绝点 y=3/4、h=27/20 给出 U=27/32>45/64，但 h<cq，故它是普通拒绝而非包络失效。
- 接受门统一为 Ucq(Y)<=p(Y)，包含边界；支配条件按一般形式写成 p<=cq 几乎处处。
- Goal 附录 B42 与旧中央清单中的“广义逆”结论属于相邻对象串项，已按 D-010 定向纠正；Goal 输入本身保持只读。
- 正文与 page wrapper 均满足“首次引用及精确数值说明 → input → FloatBarrier → 专属读图检查”。

## 字号、布局与编码

- 普通图中文字、刻度、轴标、点卡与直接标签均为 9.6pt；摘要标题为 10.2pt。
- 无 scale、xscale、yscale、resizebox、scalebox 或 transform shape。
- 摘要卡位于绘图区上方；曲线峰、cq 虚线、y=1/2 的 1/10 最小差箭头和两条直接标签均完全露出。
- p/cq 由实线/虚线区分；接受/拒绝由圆点/空心三角区分；支撑端点另用方块，浅填充表示拒绝区，灰度下不依赖颜色。
- 题注长度为 62 个源字符，只保留包络、随机点与含边界接受结论；方法与统计量放入图内摘要和图后读图检查。

## R3.2 构建与机器门

- 页包装 PDF：p577_root_r3p2_page.pdf，77,409 bytes，A4 单页。
- 独立包装 PDF：p577_root_r3p2_standalone.pdf，53,999 bytes，A4 单页。
- AUX：fig:V5-C02-rejection-envelope = 31.4 / page 576。
- 两份日志的 TeX、引用、盒警告和缺字硬模式命中均为 0。
- 字体检查：page 7 个字体、standalone 6 个字体，全部嵌入、子集化并具 Unicode 映射。
- 两份 FLS 均命中当前 v2.7.0 wrapper、公共样式与当前唯一图源。

## R3.2 三视图

- p577_root_r3p2_page_300dpi.png
- p577_root_r3p2_gray_page_300dpi.png
- p577_root_r3p2_standalone_300dpi.png

三图均为 2481x3508、300 dpi。根线程逐图实看：摘要卡、两曲线、最小间隙、浅填充、接受圆点、拒绝三角点、两候选精确分数、支撑端点、caption、读图检查和对比框均清楚；无碰撞、裁切、横向溢出、串字或灰度失辨。

## 根级裁决

根级局部验收通过，中央清单暂记“待独立复核”。只有新的独立 SA1 与隔离 SA3 均判 PASS / SPLIT_REQUIRED=NO / NEW_ISSUE=NONE 后，才可写最终接受报告并永久关闭本图。
