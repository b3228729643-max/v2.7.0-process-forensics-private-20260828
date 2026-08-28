# B-EXM-P04 构建与视觉证据 R3

## 最终构建身份

- 主线明确授予 `B_P04_R3_BUILD_SLOT_GRANTED`；启动前只读确认 `latexmk/lualatex/luatex/luahbtex` 全部为 NONE。
- 业务源码在 R2 后只做一个 token 的局部排版修复：`V3-C06.tex:615` 将 `\linebreak` 改为 `\newline`；数学、元组顺序、得分、七阶段宏、标签与引用均未改变。
- 修复后先运行 9 项内容/布局静态契约与 `git diff --check`，均 PASS。
- 从冻结的 R2 辅助目录复制到新的 R3 隔离目录，并只启动一个串行逻辑构建：

```powershell
powershell -ExecutionPolicy Bypass -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\run_background_build.ps1 `
  -Worktree D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content `
  -OutputDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P04-R3-RESUME `
  -ControlDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P04-R3-CONTROL `
  -Resume
```

- 开始：`2026-08-25T02:00:01.6933808+08:00`。
- 完成：`2026-08-25T02:17:13.0799605+08:00`。
- wrapper/child exit：`0`；构建结果：`PASS`；最终目标为 up-to-date。
- R3 期间只有同一 latexmk 串行链及其内部 lualatex 收敛轮；没有并发 TeX，没有启动 R4。
- 终态 `latexmk/lualatex/luatex/luahbtex`：NONE。

## PDF 与日志硬门

- PDF：`build/dialogue_B_content/B-EXM-P04-R3-RESUME/main_full.pdf`。
- 页数：814；页面：A4，旋转 0；PDF 版本 1.7；未加密；`Suspects: no`。
- 字节：4,947,493。
- `Output written on main_full.pdf (814 pages, 4947493 bytes)` 正常存在。
- 硬 TeX 错误：0；缺文件/I/O 错误：0；memory exhausted：0。
- Overfull：0；Underfull：0。
- 内部 rerun 原因均在同一 latexmk invocation 内收敛；最终 `All targets ... are up-to-date`。
- 保留 3 条非致命 PGF Lua `slpivtarget` 未定义提示，均明确回退到 TeX 计算；位于第 5 册既有图源，不在 P04 写域，也不影响 PDF 完成或目标页。
- 内存：3,556,178 / 4,101,490 words allocated；74,392 words still in use。
- R3 输出 19 个文件全部位于授权 RESUME/CONTROL 目录，越域输出 0。

## 覆盖页与视觉结论

目标例题在最终 814 页 PDF 中的位置如下：

| 例题 | PDF 页 |
|---|---|
| 13.1 | 223 |
| 13.2 | 227--228 |
| 14.1 | 247--248 |
| 15.1 | 262--263 |
| 16.1 | 291--292 |
| 20.1 | 382 |
| 20.2 | 389--390 |
| 21.1 | 406--407 |
| 21.2 | 416--417 |
| 22.1 | 437--438 |

- R1 以 150 dpi 渲染并逐张检查 17 页：223、227、228、247、248、262、263、291、292、382、389、390、406、407、416、417、437。
- R1 的其余 16 页全部 PASS；页 437 的八路径长行被日志量化为 25.98799pt overfull，视觉确认超过正文内宽。
- R2 使用 `\linebreak` 后 overfull 清零，但页 437 的“独立核验/枚举八条路径”产生强制两端对齐与异常字距，SA1 与主线均判定为真实视觉 FAIL。
- R3 将同一断点改为 `\newline`，重新渲染页 437--438：字距自然，八条路径和八个得分一一对应；页 438 以“解答（续）”承接“方法迁移”。
- 最终无裁切、重叠、异常拉伸、公式畸形、字符缺失、断裂边框、不可接受分页或页眉页脚异常。

最终视觉结论：`PASS`。渲染证据：

- `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P04-R1_VISUAL\page_*.png`（除已被 R3 替代的旧页 437 外，其余 16 页）。
- `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P04-R3_VISUAL\page_437.png`。
- `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P04-R3_VISUAL\page_438.png`。

## 资源锁

R3 机械终检与根级/SA1 视觉复核完成后，终态 TeX 进程为 NONE。B 不再启动 TeX，R4 明确禁止；构建锁可归还主线。
