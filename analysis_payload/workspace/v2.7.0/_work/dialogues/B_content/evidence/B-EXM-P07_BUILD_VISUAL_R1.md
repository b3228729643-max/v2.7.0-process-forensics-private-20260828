# B-EXM-P07 R1 构建、机械与视觉终检

- 批次：`B-EXM-P07`
- 结论：`VISUAL_FAIL`
- 阻塞项：`P07-VIS-001`
- 后续约束：不提交、不启动隔离 SA3、不进入 P08、不启动第二次 TeX invocation。

## 唯一构建身份

- 工作流：`run_background_build.ps1 -Resume`
- CONTROL：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P07-R1-CONTROL`
- OUTPUT：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P07-R1-RESUME`
- started：`2026-08-25T08:06:52.5632567+08:00`
- finished：`2026-08-25T08:30:27.4731890+08:00`
- wrapper / child exit：`0 / 0`
- PDF：`main_full.pdf`，818 页，A4 `595.276 x 841.89 pt`，rotation 0，PDF 1.7，未加密，`4,959,761 bytes`
- log：`main_full.log`，`249,763 bytes`
- 最终输出行：`Output written on main_full.pdf (818 pages, 4959761 bytes).`
- 构建结束后 `latexmk/lualatex/luatex/luahbtex = NONE`；`B_P07_BUILD_SLOT_RELEASED` 已发送主线。

## 机械门

- 818/818 页均为 A4、rotation 0。
- undefined control、LaTeX/package error、fatal/emergency、missing I/O、memory、undefined refs/citations、final rerun、multiply-defined、missing chars：均为 0。
- overfull/underfull hbox/vbox：均为 0。
- 符号索引：355 accepted、0 rejected、0 warnings。
- 主索引：731 accepted、0 rejected、0 warnings。
- 单一父链首遍出现的 `No file main_full.toc/symbols.ind/main_full.ind` 已在自然内部遍次闭合；最终 PDF/log 完整。

## 新 AUX 定位

| 对象 | 印刷页 | 物理页 |
|---|---:|---:|
| 33.1 | 669 | 682 |
| 34.1 | 704 | 717 |
| 34.2 | 708 | 721 |
| 34.3 | 709 | 722 |
| 34.4 | 709 | 722 |
| 35.1 | 739 | 752 |
| 35.2 | 740 | 753 |
| 35.3 | 741 | 754 |
| 36.1 | 765 | 778 |
| 36.2 | 766 | 779 |

## 视觉覆盖与结果

- 以 Poppler 150 dpi 重绘并逐页查看 23 页：物理页 `681--684`、`716--724`、`751--755`、`777--781`。
- 22/23 页无裁切、重叠、断框、公式溢出、孤立题号或异常分页；十个目标的题干、七阶段解答与相邻内容均完整。
- 唯一失败为物理页 719（印刷页 706）：页首“预测时间复杂度与空间复杂度”段落、页中第一块“读前自检”和页底第二块“读前自检”之间出现两段极大的非语义竖直空白，属于明显的 `flushbottom` 胶伸展，而非自然章节留白。
- 证据图：`B-EXM-P07-R1_VISUAL\p716-719-719.png`。
- P06-R2 同物理页对照：`B-EXM-P07-R1_VISUAL\compare_p06r2_p719.png`。对照页把两块自检及后续算法自然连续排布，不存在本轮的巨大断裂，因此该问题不能记为既有版式。

## 只读根因定位

- 可疑局部仅在 `V5-C05.tex`：印刷页 706 对应 `struct:V5-C05-CH27` 后的两个 `\paragraph` 自检块，以及紧随其后的不可拆 `AlgorithmContract` / `[H]` algorithm。
- P07 对例 34.1 的七阶段扩写使后续分页边界发生变化；算法整体移到下一页后，合并总册的 `\flushbottom` 把留在页 719 的段前/段间可伸缩竖直胶放大。
- 这是基于源码结构、P06-R2 对照与 R1 页面表现的 root inference；尚未修改任何源码。任何局部刚性间距或 keep-with-next 修复均须主线另行授予精确源码范围与新构建槽，且不得修改共享宏。

## 路由

`B_P07_R1_VISUAL_FAIL / P07-VIS-001`：机械 PASS、视觉 FAIL。保持四个业务源码文件当前差异冻结；等待主线裁决，不派 SA3、不提交、不再启动 TeX。
