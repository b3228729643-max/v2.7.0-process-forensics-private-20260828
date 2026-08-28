# FIG-P596-01｜ROOT-APPLY-R3.1

## 结论

- `PASS_LOCAL_PENDING_INDEPENDENT`
- `SPLIT_REQUIRED=NO`
- R3 两份 PDF 与机器门通过，但彩色、灰度和 standalone 三图均显示“证书止于平稳”范围框覆盖“另行核验链结构”框，故根线程判视觉失败并保留全部 R3 工件。R2.2 将范围框移到右侧平稳/时间平均节点之间；R3.1 的源码、机器门与三视图全部通过。

## 对象与身份

- canonical UID：`FIG-P596-01`
- legacy ID：`FIG-V5-C03-01`
- label：`fig:V5-C03-dependency`
- 唯一图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_dependency_graph.tex`
- 单图约束：figure、tikzpicture、caption、label、combined alt 各1；不拆图。
- 页级定位：图32.1，页595。

## 数学与教学语义

- 目标分布与提议经接受率构造 MH 核 `K`；细致平衡等式只作为 `πK=π` 的充分证书，不推出不可约、遍历性或时间平均。
- 遍历时间平均另走链结构分支：有限状态使用不可约性，一般状态空间使用正 Harris 常返；非周期性没有被错误加入时间平均前提。
- 边缘分布收敛在相应不可约/Harris结构条件上再加入非周期性，与时间平均结论分离。
- 图只说核通常形成相关轨迹，并以独立核 `K(x,dy)=π(dy)` 反驳“任意核必然相关”；轨迹、自相关、MCSE与ESS被定位为诊断。
- 正文、page wrapper、图、题注和 combined alt 均采用同一作用域；首次引用后为图输入、`FloatBarrier` 和专属读图检查。

## 字号、拓扑与灰度门

- 图内普通可见文字和线例均为9.6pt；无更小字号声明，无总体 `scale`、`resizebox`、`scalebox` 或 `transform shape`。
- 10条逻辑边均为独立 `draw[->]`；MH构造、平稳证书、结构条件与相关性诊断分别用实线、虚线、点划线和点线，并辅以不同节点边框。
- 上方构造/证书通道、左下诊断通道和右下结构/收敛通道无线交叉。
- R3.1 范围说明位于平稳节点下方、时间平均节点上方，与结构框横向分离；三视图均确认无覆盖、碰撞或裁切。

## R3.1 构建与机器门

- page：`p596_root_r3p1_page.pdf`，63,402 bytes，A4单页。
- standalone：`p596_root_r3p1_standalone.pdf`，47,320 bytes，A4单页。
- AUX：`fig:V5-C03-dependency = 32.1 / page 595`。
- 两份最终日志对致命错误、未定义引用、重复标签、Overfull/Underfull 和缺字硬模式命中均为0。
- page 5个字体、standalone 3个字体，全部嵌入、子集化并带 Unicode 映射。
- 两份 FLS 均命中 v2.7.0 wrapper、`release_version.tex`、公共图样式与当前唯一图源。
- V5-C03 source JSON 为10图且P596 canonical UID唯一；中央 CSV 为99行×19列、99个唯一 UID 且P596唯一。

## R3.1 三视图

- `p596_root_r3p1_page_300dpi.png`
- `p596_root_r3p1_gray_page_300dpi.png`
- `p596_root_r3p1_standalone_300dpi.png`

三图均为2481×3508、300 dpi。根线程逐图实看：范围框、结构框、平稳/时间平均节点、10条箭头、四类线型与线例、题注和图后检查均清楚；无碰撞、裁切、串字或灰度失辨。

## 根级裁决

根级局部验收通过，中央清单暂记“待独立复核”。只有新的隔离 SA1 与独立 SA3 均判 `PASS / SPLIT_REQUIRED=NO / NEW_ISSUE=NONE` 后，才可写最终接受报告并冻结本图。
