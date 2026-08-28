# B-EXM-P05 R3 构建与视觉证据

## 构建身份与资源锁

- 主线授权：`B_P05_R3_BUILD_SLOT_GRANTED`。
- 启动前 `latexmk/lualatex/luatex/luahbtex`：NONE。
- 从冻结的 P05 R2 输出复制 14 个有效辅助文件至全新隔离目录 `B-EXM-P05-R3-RESUME`；控制根为 `B-EXM-P05-R3-CONTROL`。
- 仅启动一个既有 `run_background_build.ps1 -Resume` invocation：latexmk 父 PID 16340；内部依次自然运行 lualatex PID 14972、18008。没有第二个 latexmk、独立 invocation、并发 TeX、自动重试或 R4。
- 开始：`2026-08-25T04:44:30.4648040+08:00`。
- 完成：`2026-08-25T05:00:02.9654537+08:00`。
- wrapper/child exit：`0`；构建结果：`PASS`；最终目标 up-to-date。
- 自然结束后 `latexmk/lualatex/luatex/luahbtex`：NONE；已向主线发布 `B_P05_R3_BUILD_SLOT_RELEASED`，并单独更正完成时间为上述 CONTROL 记录。B 不再启动 TeX。

## PDF、日志与索引机械门

- PDF：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P05-R3-RESUME\main_full.pdf`。
- 815 页，4,948,175 bytes；全部页面 `595.276 x 841.890 pt`、A4、旋转 0；PDF 未加密。
- 硬 `!` 错误、LaTeX Error、fatal/emergency、缺文件/I/O、memory exhausted、undefined control sequence、undefined references/citations、missing characters：全部 0。
- Overfull：0；Underfull：0。
- 主索引：731 accepted、0 rejected、0 warnings。
- 符号索引：355 accepted、0 rejected、0 warnings。
- 保留 3 条既有 PGF `slpivtarget` fallback，不属于 P05 写域。

机械结论：`PASS`。

## 视觉覆盖

Poppler 150 dpi 渲染物理页 210--212、231--233、337--340、453--455，共 13 页。证据位于：

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P05-R3_VISUAL\page-*.png`

逐页检查结论：

- 页210--212：页211无孤立“【原书练习整理】”；标题与练习12.1共同位于页212。无裁切、重叠或断裂边框。
- 页231--233：页232无孤立标题；标题与练习13.1共同位于页233。无裁切、重叠或断裂边框。
- 页337--340：算法18.1结束、18.10节、例题18.1解答及续页结构完整。页338标题后的留白恢复自然，页339续框与后续内容衔接正常；无内容丢失、裁切、重叠或边框断裂。
- 页453--455：23.6节、例题23.1解答及后续自检内容完整。页454标题后的留白恢复自然；无内容丢失、裁切、重叠或边框断裂。

## R2 → R3 定量比较

以 Poppler bbox 的标题首词与 solution 框首词“读题翻译”的 `yMin` 差值衡量可见间距：

| 物理页 | R2 间距 | R3 间距 | 减少量 | 降幅 |
|---|---:|---:|---:|---:|
| 338 | 87.113 pt | 26.695 pt | 60.418 pt | 69.36% |
| 454 | 84.094 pt | 26.695 pt | 57.399 pt | 68.25% |

- 页338：标题 `yMin=256.818456`；R2 solution 首词 `343.931456`，R3 `283.513456`。
- 页454：标题 `yMin=148.568456`；R2 solution 首词 `232.662456`，R3 `175.263456`。
- 两页 R2/R3 PNG 均非逐字节相同，且肉眼检查与定量结果一致；局部刚性 `\smallskipamount=3pt` 已消除 flushbottom 放大的异常伸展。
- 页211/232的分页修复未回归，标题分别与首题共同位于页212/233。

视觉结论：`PASS`。

## R3 源码边界

- P05 累计仍为 9 个授权章节文件、10 道例题。
- R3 增量仅 V3-C02 与 V3-C07 两个既有局部组加入 `\setlength{\smallskipamount}{3pt}`；V2-C01/V2-C02 的 R2 `\Needspace` 移动保持不变。
- 未修改共享宏、负 `vspace`、文字、数学、标签、引用、绘图源码、测试或其他文件。

R3 构建与视觉总判定：`PASS`。允许进入完全 fresh post-fix SA1 与全新隔离 SA3；不授权任何进一步 TeX invocation。
