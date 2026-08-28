# FIG-P580-01｜ROOT-APPLY-R3.2

## 裁决

- `RESULT=FAIL_SAFETY_MARGIN`
- `SPLIT_REQUIRED=NO`
- 不更新中央 CSV / numeric manifest，不启动修复后 SA1/SA3。

## 本轮对象

- SA2 源级轮次：`R2.3`。
- 图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_is_support.tex`。
- 新 jobname：`p580_root_r3p2_page`、`p580_root_r3p2_standalone`。
- page PDF：69,443 bytes；standalone PDF：42,494 bytes；均为 A4 单页。
- AUX：图 31.6，逻辑页 579。
- 两份日志按项目硬模式扫描均为 0；FLS 均命中 v2.7.0 wrapper、`release_version.tex`、公共图样式和当前唯一图源。
- page 7 个字体、standalone 5 个字体，全部嵌入、子集化并带 Unicode 映射。
- 三类原生证据均为 2481×3508、300dpi：彩色 page、灰度 page、standalone。

## 通过项

- 旧接受轮横向溢框已经消失：三个比率改为三列三行后，卡片、标题、三列表头和三列数值均完整位于右面板内。
- 卡片左边与纵轴、卡片底边与峰值曲线/中心方点、卡内三行横向间距在 1:1 ROI 中均未见重叠。
- 普通文字与刻度为 9.6pt、两面板标题为 10.2pt；同类跨面板字号一致，无整体缩放和低字号别名。
- 三条解析密度、支持关系、缺失质量和 `0.96/1.50/0.96` 三个比率未回归。

## 阻断像素证据

严格协议要求把任意非纯白抗锯齿像素计入实墨，并以连续纯白原生像素计净空；返修候选采用至少 12px 安全门。

- standalone：比率卡下边框的 AA 实墨延伸至 `y=578`；蓝色“实线 $p(x)$”标签的 AA 实墨从 `y=579` 开始，且横向投影重合。因此连续纯白行数为 **0px**，属于边框与文字接触。
- 彩色 page：同一对象分别延伸至 `y=888` 与从 `y=889` 开始，连续纯白行数同为 **0px**。
- 灰度 page：对应行与彩色 page 完全一致，仍为 **0px**。
- 1:1 证据：`p580_root_r3p2_roi_card_label_tight_1to1.png`、`p580_root_r3p2_roi_card_all_1to1.png`、`p580_root_r3p2_roi_card_curve_point_1to1.png`。

该接触在全图缩略视图中容易被误判为正常留白，但在原生像素下是明确 FAIL。预计源坐标预算不能替代实际渲染测量。

## 下一步

退回同一专属 SA2，只调整卡片/标签的纵向排布；不得改数学、字号、三种点形、caption、label、alt、UID 或其他文件。下一候选须同时保证：卡片下边框到“实线 $p(x)$”标签、曲线、中心方点至少 12px；卡片顶边到轴域上界至少 12px；卡内各行及卡片左右边到轴/面板边界至少 12px。
