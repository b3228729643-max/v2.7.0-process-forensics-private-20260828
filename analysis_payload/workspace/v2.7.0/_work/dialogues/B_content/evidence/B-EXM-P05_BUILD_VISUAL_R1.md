# B-EXM-P05 构建与视觉证据 R1

## 构建身份

- 主线明确授予 `B_P05_BUILD_SLOT_GRANTED`；启动前两次只读确认 `latexmk/lualatex/luatex/luahbtex` 全部为 NONE。
- 从同一 B 分支冻结的 P04 R3 辅助目录复制 14 个种子文件到新的 P05 R1 隔离输出目录；准备阶段未启动 TeX。
- 仅启动一个串行逻辑构建及其 latexmk 自然内部遍次：

```powershell
powershell -ExecutionPolicy Bypass -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\run_background_build.ps1 `
  -Worktree D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content `
  -OutputDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P05-R1-RESUME `
  -ControlDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P05-R1-CONTROL `
  -Resume
```

- 开始：`2026-08-25T03:25:31.2787408+08:00`。
- 完成：`2026-08-25T03:43:05.0710859+08:00`。
- wrapper/child exit：`0`；构建结果：`PASS`；最终目标为 up-to-date。
- 第一遍后因标签变化由同一 latexmk PID 21852 自然触发第二遍；没有第二个 latexmk、没有并发或独立 invocation。
- 构建后 `latexmk/lualatex/luatex/luahbtex`：NONE。

## PDF 与日志硬门

- PDF：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P05-R1-RESUME\main_full.pdf`。
- 页数：815；页面：A4，旋转 0；PDF 版本 1.7；未加密；`Suspects: no`。
- 字节：4,948,771。
- `Output written on main_full.pdf (815 pages, 4948771 bytes)` 正常存在。
- 硬 TeX 错误：0；缺文件/I/O 错误：0；memory exhausted：0。
- Undefined references/citations：0；missing characters：0。
- Overfull：0；Underfull：0。
- 主索引接受 731 项、拒绝 0、警告 0；符号索引接受 355 项、拒绝 0、警告 0。
- 保留 3 条第5册既有 PGF Lua `slpivtarget` 未定义提示，均回退到 TeX 计算；不在 P05 写域，不影响目标页或 PDF 完成。
- 输出目录 14 个文件、控制目录 5 个文件；均位于 B 工作树的授权 P05 R1 目录。

## 覆盖页定位

前置页共 13 页，目标例题的正文页由最终 `main_full.aux` 确认，物理 PDF 页如下：

| 例题 | PDF 页 |
|---|---|
| 8.2 | 141 |
| 9.1 | 152--153 |
| 10.1 | 168 |
| 12.1 | 202--203 |
| 12.3 | 211 |
| 13.3 | 231--232 |
| 15.2 | 273--274 |
| 17.1 | 311--312 |
| 18.1 | 338--339 |
| 23.1 | 454 |

## 视觉结论

- 使用 Poppler `pdftoppm` 以 150 dpi 渲染全部 16 个覆盖页。
- 逐页检查正文、题框、解答框、公式、数组/表格、页眉页脚、导航和章节衔接。
- 9.1、12.1、13.3、15.2、17.1、18.1 的跨页均以规范的“解答（续）”承接，内容连续。
- 12.3、13.3 的 `SLRunningExample` 已独立位于 solution 结束后，边框和语义分区清楚。
- 18.1 的扩写使第18章较 P04 基线增加一页；第19章起整体顺延一页。增页页 338--339 的表格、联合 KKT 条件、结论与后续复杂度框均自然分页，无空白页或孤立标题。
- 23.1 顺延后的页 454 仍为完整单页解答，召回率、延迟、可行集与最终选择无裁切。
- 裁切 0、重叠 0、异常拉伸 0、公式畸形 0、字符缺失 0、断裂边框 0、不可接受分页 0、页眉页脚异常 0。

最终视觉结论：`PASS`，16/16 页通过。

渲染证据：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P05-R1_VISUAL\page_*.png`。

## 资源锁

- 机械日志门与 16 页视觉终检后，TeX 进程为 NONE。
- B 不再启动 TeX；P05 R2 未获授权且未启动，构建锁可归还主线。
