# FIG-P634-01｜R94 官方全书冻结与根预检

- 官方产物：`src/build/strict_current_r94_fullbook/main_full.pdf`
- 构建：退出码 `0`，`813` 页，`4,934,451` bytes；全部页面唯一尺寸为 A4 `595.276 × 841.89 pt`、旋转 `0`。
- 硬日志门：LaTeX error、fatal/emergency、未定义引用/引文、multiply-defined、duplicate destination、overfull box 共 `0` 命中。
- 其余 `15` 条均为非致命诊断：6 条 hyperref PDF-string、2 条 unicode-math、1 条 microtype、1 条包路径提示、3 条 pgfplots Lua-survey 转 TeX 后端、2 条 imakeidx 提示；`slpivtarget` 的 3 条回退与 R93 相同，不是引用未定义。

## 独立页面定位

以“**一轮系统扫描的坐标带**”和“**系统扫描按固定次序立即写回**”在官方 PDF 全书检索，只命中物理第 `682` 页；该页印刷页码为 `669`，题注编号为标准自动编号“**图 33.3**”。

先将整张物理页直接栅格化为 300 dpi `2481 × 3508 px` 与 200 dpi，再从 300 dpi 整页按像素框 `[280,1690,2235,2575]` 切出 `1955 × 885 px` 图与题注区域，没有使用 PDF clip 作为最终几何。根角色已在 native 300 dpi 彩色与灰度切片查看：未见可见重叠、裁切或突兀字号，标题、八个坐标槽、状态卡、箭头和题注可读。

## 判定边界

本记录只把 R94 官方产物冻结并放行给全新的隔离 SA1；它**不是** FIG-P634-01 的最终通过。SA1 必须重新完成逐字 raw H_ink、D/E、全对象全无序 pair、纹理 paint-order、标点、语义与整体和谐门；若 SA1 通过，还必须由全新的 SA3 再审，最后才由 root 作最终裁决。
