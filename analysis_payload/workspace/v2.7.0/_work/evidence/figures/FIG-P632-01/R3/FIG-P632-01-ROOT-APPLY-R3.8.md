# FIG-P632-01｜ROOT APPLY R3.8

RESULT: **ROOT_PASS_PENDING_INDEPENDENT_SA1_SA3**  
SPLIT_REQUIRED: **NO**

## 候选与机器门

- 来源：SA2-R2.6；仅把上下同型公式 node 从 (0.45,2.68) 同步移到 (0.55,2.68)。R2.5 双行标签及全部数学、曲线、轴、路径与警示框不变。
- 页面 PDF：p632_root_r3p8_page.pdf，82148 bytes。
- 独立 PDF：p632_root_r3p8_standalone.pdf，50302 bytes。
- 三类证据：p632_root_r3p8_page_300dpi.png、p632_root_r3p8_gray_page_300dpi.png、p632_root_r3p8_standalone_300dpi.png，均为对应 PDF 原生 300 dpi、2481×3508。
- TeX Live 2026 LuaLaTeX；两日志硬模式命中 0。两 PDF 均为 A4 单页；AUX 为图 33.2、逻辑页 664；FLS 命中当前 wrapper、公共样式、版本源和精确 P632 图源。
- 页面版 8 种、独立版 4 种字体全部 emb=yes/sub=yes/uni=yes。
- 源级唯一全局可见 node 字号为 9.6/11.5 pt；无低字号覆盖、transform shape、resizebox/scalebox 或总体缩放。

## 1:1 原生像素测量

所有数值把任意非纯白抗锯齿像素计入实墨；坐标均来自 R3.8 standalone 300 dpi 的未缩放 ROI。矩形 bbox 分离给出保守下界，真实稀疏轮廓距离只会更大。

| 交互对象 | 保守连续纯白净空 |
|---|---:|
| 上积分号—上纵轴 | 23 px |
| 下积分号—下纵轴 | 22 px |
| 上双行标签—上纵轴/箭头走廊 | 18 px |
| 上双行标签—映射路径 | 32 px |
| 上双行标签—外等高线 | 75 px |
| 下双行标签—映射路径 | 42 px |
| 下双行标签—下纵轴 | 124 px |
| 下双行标签—积分/公式区 | 144 px |
| 下双行标签—外等高线 | 58 px |

彩色页、灰度页和独立图的总览及紧 ROI 均逐张以 original/1:1 查看；未见文字/公式与轴、曲线、箭头、刻度、边框、另一面板或裁剪边界接触，也未见 1--3 px 邻域。上、下公式右移后仍处于条件面板上方自然留白，右端分式、>0 和最大值公式均未越界或压迫曲线。

主要 ROI：

- p632_root_r3p8_roi_standalone_all_1to1.png
- p632_root_r3p8_roi_standalone_upper_label_1to1.png
- p632_root_r3p8_roi_standalone_lower_label_1to1.png
- p632_root_r3p8_roi_standalone_upper_integral_axis_1to1.png
- p632_root_r3p8_roi_standalone_lower_integral_axis_1to1.png
- p632_root_r3p8_roi_page_all_1to1.png
- p632_root_r3p8_roi_gray_all_1to1.png

## 字体与层级根检查

- 普通 CJK、Latin、数学说明和刻度均继承 9.6 pt；上下两个同型条件面板使用完全相同的公式样式、基线和行距。
- 两条双行映射标签与普通图内说明同层级，没有通过缩小字号取得净空；关键公式虽有大运算符自然高度，但未视觉主导曲线或侵占相邻对象。
- 彩色与灰度下，标签、切片、等高线和两条条件曲线仍可由颜色加线型/结构冗余识别。

## 反回归

- rho=3/5、a=1、b=4/5，条件均值 12/25 与 3/5、共同方差 16/25、两边缘分母及两条积分为 1 的数学内容未改。
- 图号 33.2、逻辑页 664、caption、label、alt、零边缘正则条件版本说明均未改。
- 单 figure、单 tikzpicture；无 UID、wrapper、JSON、CSV、章节或公共样式改动。

根线程视觉门通过，但不据此最终关闭。必须由两个全新、彼此独立的只读审查实例按 STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md 自制紧 ROI、实测字体层级并分别通过，之后才可写 ROOT-ACCEPTANCE。

RESULT=ROOT_PASS_PENDING_INDEPENDENT_SA1_SA3
