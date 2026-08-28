# FIG-P583-01 / R103 / R168 完全 fresh isolated SA1 正式报告

## 身份与边界

- Reviewer UID：`/root/p583_r103_fresh_sa1`
- HANDOFF_ID：`A-R103-P583-SA1-FRESH-20260825`
- 实例：完全 fresh isolated SA1；未继承或读取任何旧 FIG-P583-01 evidence、SA1/SA2/SA3、root 报告、候选截图、state、inventory、git history/diff 或聊天旧结论；未派生子代理。
- Model/effort：`gpt-5.6-sol/xhigh`
- 唯一证据根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P583-01\STRICT_R1_SA1_FRESH_R103_R168_20260825`
- 图源只读；未运行 LuaLaTeX、latexmk、luatex、luahbtex 或任何 TeX 引擎；未修改源码、PDF、中央 state/inventory，也未提交 Git。

## 冻结候选

- 官方 R103 PDF：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf`
- 物理页：633（印刷页 620，图 31.9）
- 身份：817 页，A4 `595.276×841.890 pt`，`4,967,184 bytes`
- SHA-256：`9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`
- 身份与任务冻结值逐项一致。

## 原生证据重建

- 300 dpi 整页：`2481×3508 px`
- 200 dpi 整页：`1654×2339 px`
- figure crop：整页像素 `[250,250,2180,1055]`，`1930×805 px`
- chart standalone：整页像素 `[570,250,1842,913]`，`1272×663 px`
- 300 dpi 测量图只做整数裁剪，不做 resize；8× nearest 仅供人工逐像素观察，不回写计数。

## 完整对象与关系分母

- Glyph：71 个（G001–G071）
- final-visible Graphic：19 个（P001–P019）
- 总对象：`N=90`
- 全部无序 pair：`C(90,2)=4005`，实际 4005 行，无缺行、重复或方向重复。
- Critical：18 个；其中注释文字到速率三角 5 个、条件节点文字到边框 13 个。
- 公式路径规则：0；`O(N^{-1/2})` 完全由 PDF 字符流覆盖。
- 图体 PDF drawing group 10 个全部归属；19 个前景 graphic 对象、2 个白色 background/occluder 角色，无未归属 visible path。

## 机器硬门

- `MACHINE_HARD_GATES=PASS`
- `MACHINE_FINAL_CROSSCHECK=PASS`
- empty mask：0
- foreign-pixel glyph bbox：0
- unique object/safe filename：90/90
- 普通 mask PNG：90/90
- 非法 overlap pair：0；`OVERLAP_PIXEL_COUNT=0`
- clearance failure：0
- `CLIP_PIXEL_COUNT=0`
- 独立 text–text 最小 bbox 净空：33.242 px（门槛 4）
- text/formula–line/marker 最小 raw-mask 净空：5 px（门槛 3）
- node text–final-visible border 最小净空：13 px（门槛 5）
- text–chart crop edge 最小净空：20 px（门槛 6）
- 21 个非零交集均为明确设计关系：16 个同父公式/轴系统连接、4 个坐标几何连接、1 个曲线–三角速率构造。后者 36 个共享像素表达同一 `×4/÷2` 斜率，不是非法碰撞。

## 真实人工观察分母

- 实际打开 9/9 glyph contact sheets；逐 ID 人工账 71/71，全部 original-match、overlay-complete、mask-only-pure，missing-stroke=0、foreign-pixel=0。
- 实际打开 3/3 graphic contact sheets；逐 ID 人工账 19/19，同样全部闭合。
- 实际打开 3/3 critical contact sheets；18/18 critical pair 已看。三角注释净空为 5、6、5、7、8 px；节点文字到边框为 13–15 px。
- 实际打开完整 pair 矩阵、语义关系 overlay、逐 glyph overlay、curve–triangle 1× key overlay、彩色 crop、standalone、灰度图和 200 dpi 整页。
- 手工 pair 视觉账按 R168 合并为 9 个同类组；其中 pair 分类分解严格覆盖全部 4005 行。

## 字体与 R168 判定

- 源级：tick 8.6 pt；default/triangle note/condition node 9.2 pt；axis label/rate formula 9.6 pt；无 scale/resize transform。
- 低于旧 9.5 pt 绝对门的声明在本任务 R168 下只作为 advisory，因为最终 300 dpi 和整页视图实际清楚、协调，无严重失衡。
- 逐像素参考值有 3 个 advisory：G035 上标 Unicode 减号为完整低轮廓 7 px；纵排 `S` G070 为 19 px，`E` G071 为 23 px。三者均 codepoint 正确、轮廓完整且肉眼清楚。
- 轴标题/自然上标的 ratio 告警由不同字形固有轮廓与低轮廓运算符 taxonomy 引起，没有字号缩放异常。
- 未见 tofu、缺字、错误字形/codepoint、数学语义错误、实际不可读、严重失衡、真实裁切或重叠。
- `FONT_VISUAL_HARMONY_PASS=true`。

## 图形、数学与图文一致性

- log-log 曲线和标签均为 `O(N^{-1/2})`。
- 三角形从 `(16,1/4)` 到 `(64,1/8)` 正确表达样本量 `×4`、RMSE 约 `÷2`。
- 条件框 `iid 且方差有限` 与题注一致；题注正确说明相关样本或无限方差不能直接沿用该直线。
- 横纵轴、刻度、公式、对象内容与题注一致。
- 灰度下曲线、三角与条件框仍可区分；整页融合自然，无拥挤、裁切或后续例题碰撞。

## 最终判定与路由

正式 fresh isolated SA1 verdict：**PASS**。

唯一允许路由：`SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`。

本实例不启动 SA3，不写 `A_LOCAL_PASS`，不更新中央 inventory/state。证据根以双 manifest（`MANIFEST.json`、`MANIFEST.sha256`）和严格最后标记 `WRITE_STOPPED` 封存；该报告与 handoff 位于证据根外并设为只读。
