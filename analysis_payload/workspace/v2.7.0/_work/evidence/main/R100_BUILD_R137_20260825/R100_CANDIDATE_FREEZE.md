# R100 官方候选冻结记录

- 冻结时间：`2026-08-25T00:35:31+08:00`
- 主线提交：`81d7c7ad150a9306ae3599fe9c15f4c8bb125d9a`
- 集成内容：B-EXM-P03 主线提交 `23de9f5db8a961e26f6614f38720e389f144134b`、公共分册入口提交 `49b7622299f195a53ce2f429f2fde963c6950b84`、P654 主线提交 `81d7c7ad150a9306ae3599fe9c15f4c8bb125d9a`
- 官方候选：`R100`
- PDF：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r100_fullbook\main_full.pdf`
- 物理页数：`814`
- 字节数：`4,943,206`
- SHA-256：`5B1E4B4C5D64A0CA49833F38ED28C4397392BF5E50503431F3170614DF63D171`

## 构建判定

- `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r100_fullbook -NoPublish` 最终退出码 `0`，新目录全量构建由 latexmk 自行收敛，未并发启动第二条 TeX 链。
- `symbols.idx`：355 entries accepted，0 rejected，0 warnings。
- `main_full.idx`：731 entries accepted，0 rejected，0 warnings。
- 最终 `main_full.log` 中 LaTeX/Package error、undefined control/reference、duplicate、fatal、emergency、runaway、capacity、memory exhausted、rerun 和 over/underfull 计数全部为 0；`Output written` 精确 1 次。
- PDF 为 814/814 页 A4、无旋转；14 组字体全部嵌入且含 Unicode 映射。
- 导航审计 `PASS`：5 册、37 章、双索引、273 bookmarks、4,952 internal links、7,419 named destinations；无无效书签/链接、无意外版本字符串。
- 主线工作树冻结时 clean，TeX 进程为 NONE。

## 受影响页视觉抽检

- B-EXM-P03：物理页 17、18、29、30、48、49、62、65、67、68、81、99、100、115、116、121、122，共 17/17 页 PASS。
- FIG-P654-01：物理页 702，整图、题注、相邻读图说明与后续表格页面集成 PASS。
- 未见裁切、非法重叠、公式畸形、字符缺失、断裂续页或页眉页脚异常。
- 150 dpi 页图和三张 contact sheet 位于 `affected_pages_150dpi/`。

## 路由边界

R100 已回派给 Dialogue A，供 FIG-P654-01 完全全新隔离 SA1 使用；同时官方构建槽归还 P608 窄修复 SA2。R100 是阶段候选，不等于 P654 `A_LOCAL_PASS`、99 图总门或最终全书发布。
