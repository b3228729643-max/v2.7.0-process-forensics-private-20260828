# B-EXM-P05 R2 构建与视觉证据

## 构建身份

- 主线授权：`B_P05_R2_BUILD_SLOT_GRANTED`。
- 启动前 `latexmk/lualatex/luatex/luahbtex`：NONE。
- 从冻结的 P05 R1 输出复制 14 个有效辅助文件至全新隔离目录 `B-EXM-P05-R2-RESUME`。
- 仅启动一个 `-Resume` invocation：latexmk 父 PID 14220；内部依次自然运行 lualatex PID 9740 与 22400。没有第二个 latexmk、独立 invocation、并发 TeX 或 R3。
- 开始：`2026-08-25T04:11:19.7911534+08:00`。
- 完成：`2026-08-25T04:28:14.2879978+08:00`。
- wrapper/child exit：`0`；构建结果：`PASS`；最终目标 up-to-date。
- 完成后 TeX 进程：NONE。

## PDF、日志与索引机械门

- PDF：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P05-R2-RESUME\main_full.pdf`。
- 815 页，4,948,176 bytes；全部页面 `595.276 x 841.890 pt`、A4、旋转 0；PDF 1.7，未加密，`Suspects: no`。
- 硬 `!` 错误、LaTeX Error、fatal/emergency、缺文件/I/O、memory exhausted、undefined control sequence、undefined references/citations、missing characters：全部 0。
- Overfull：0；Underfull：0。
- 主索引：731 accepted、0 rejected、0 warnings。
- 符号索引：355 accepted、0 rejected、0 warnings。
- 保留 3 条既有 PGF `slpivtarget` fallback，不属于 P05 写域。

机械结论：`PASS`。

## 视觉覆盖

Poppler 150 dpi 渲染物理页 210--212、231--233、337--340、453--455，共 13 页。证据位于：

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P05-R2_VISUAL\page-*.png`

### 已通过

- 页210--212：页211底部不再出现孤立“【原书练习整理】”；标题与练习12.1共同位于页212，页210--212无裁切、重叠或断裂边框。
- 页231--233：页232底部不再出现孤立标题；标题与练习13.1共同位于页233，页231--233无裁切、重叠或断裂边框。
- 页337、339--340、453、455：相邻内容与分页衔接正常，无内容丢失或新增页数顺延。

### 阻断失败

- 页338：例题18.1解答标题到 solution 框的异常留白仍存在。
- 页454：例题23.1解答标题到 solution 框的异常留白仍存在。
- 两页 R2 PNG 与对应 R1 PNG 逐字节完全相同：`PAGE_338_PNG_BYTE_IDENTICAL=True`，`PAGE_454_PNG_BYTE_IDENTICAL=True`。
- Poppler bbox 坐标也与 R1 完全相同：
  - 页338：标题首词 `yMin=256.818456`，solution 首词“读题翻译” `yMin=343.931456`。
  - 页454：标题首词 `yMin=148.568456`，solution 首词“读题翻译” `yMin=232.662456`。
- 因而局部 `\let\needspace\Needspace` 未改变这两页的可见排版，主线要求的“异常伸展必须消失”未满足。

视觉结论：`FAIL`。R2 构建本身有效，但不能进入 fresh post-fix SA1、全新隔离 SA3、提交或 P06。

## 后续路由建议（未应用）

共享宏显示标题尾部仍执行 `\par\nobreak\smallskip`；`\smallskipamount` 含可伸缩分量，可能在 flushbottom 页吸收原本由 lowercase `\needspace` 承担的剩余伸展。一个保持 nominal 3pt、只作用于目标调用的候选是：

```tex
{\let\needspace\Needspace\setlength{\smallskipamount}{3pt}\SLExampleSolutionHeading{...}}
```

该建议尚未获主线授权、未写入源码、未构建。R3 禁止自行启动。

## 资源锁

- 机械与视觉终检后 `latexmk/lualatex/luatex/luahbtex` 全部 NONE。
- B 不再启动 TeX；构建槽可归还主线。
