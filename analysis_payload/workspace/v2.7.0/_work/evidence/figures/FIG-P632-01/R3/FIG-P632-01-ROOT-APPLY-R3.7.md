# FIG-P632-01｜ROOT APPLY R3.7

RESULT: **FAIL_SAFETY_MARGIN**  
SPLIT_REQUIRED: **NO**

## 候选

- 来源：SA2-R2.5；两条映射说明重排为 9.6 pt 双行，无白底、无整体缩放。
- 页面 PDF：p632_root_r3p7_page.pdf，82150 bytes。
- 独立 PDF：p632_root_r3p7_standalone.pdf，50302 bytes。
- 彩色页、灰度页、独立图均由对应 PDF 原生导出为 300 dpi、2481×3508。

## 机器门

- TeX Live 2026 LuaLaTeX；两日志硬模式命中 0。
- 两 PDF 均 A4 单页；AUX 为图 33.2、逻辑页 664；FLS 命中当前 wrapper、公共样式、版本源和 P632 图源。
- 页面版 8 种、独立版 4 种字体全部嵌入、子集化并有 Unicode 映射。
- 源级 every node=9.6/11.5 pt，无 tiny/scriptsize/footnotesize、整体缩放或白底规避。

## 原生像素结论

R2.5 已消除两条映射标签的既有接触；1:1 ROI 显示上、下标签不再碰外等高线、路径、箭头、纵轴、积分号或曲线。标签到邻近对象的保守连续非白像素净空均达到或超过 12 px。

但将全部抗锯齿像素计入实墨后：

- 上积分号与纵轴连续纯白净空为 11 px；
- 下积分号与纵轴连续纯白净空为 10 px。

二者均超过协议的 4 px 最低门，但低于本轮为避免脆弱放行预设的 12 px 安全余量，因此根线程主动不放行。交回专属 SA2，只允许上下公式节点同步小幅右移，不改变公式、曲线、轴、路径、双行标签、警示框、字号和缩放契约。

RESULT=FAIL_SAFETY_MARGIN

