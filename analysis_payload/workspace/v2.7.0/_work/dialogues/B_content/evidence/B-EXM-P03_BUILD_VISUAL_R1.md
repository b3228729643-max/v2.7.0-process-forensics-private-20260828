# B-EXM-P03 构建与视觉证据 R1

## 资源互斥与构建路线

- A 明确发布 `A_P654_BUILD_SLOT_RELEASED`；启动前只读复核 `latexmk/lualatex/luatex/luahbtex` 为 NONE。
- 从冻结的 B-P02 R7 辅助目录只读复制到新的 B-P03 隔离目录；未修改 P02 输出或证据。
- 单一逻辑命令：

```powershell
powershell -ExecutionPolicy Bypass -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\run_background_build.ps1 `
  -Worktree D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content `
  -OutputDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P03-R1-RESUME `
  -ControlDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P03-R1-CONTROL `
  -Resume
```

- 开始：`2026-08-24T23:45:02.8712105+08:00`。
- 完成：`2026-08-24T23:54:39.1409268+08:00`。
- wrapper/child exit：`0`。
- 构建期间始终只有本次 latexmk 进程链；未启动第二个构建。
- 终态检查时 TeX 进程为 NONE，受控构建锁已释放。

## PDF 与日志硬门

- PDF：`build/dialogue_B_content/B-EXM-P03-R1-RESUME/main_full.pdf`。
- 页数：814。
- 页面：A4，595.276 x 841.89 pt，旋转 0。
- 字节：4,943,198。
- PDF 版本：1.7；未加密；`Suspects: no`。
- `main_full.log` 正常结束：`Output written on main_full.pdf (814 pages, 4943198 bytes)`。
- `Output written`：1。
- `!`/LaTeX/Package/Fatal/Emergency/Undefined control sequence/Runaway/TeX capacity：0。
- `memory exhausted`：0。
- Overfull/Underfull hbox/vbox：0。
- stderr 中只有已知 Perl locale warning 与正常 makeindex/latexmk 诊断；真实子进程退出码已正确保留为 0。

## 文本定位与视觉页

使用 Poppler 文本定位后，按 PDF 技能以 150 dpi 渲染并在原始分辨率逐张目检 17 个完整覆盖页：

| 例题 | PDF 页 |
|---|---|
| 1.1 | 17--18 |
| 2.1 | 29--30 |
| 3.1 | 48--49 |
| 4.1 | 62 |
| 4.2 | 65 |
| 4.3 | 67--68 |
| 5.1 | 81 |
| 6.1 | 99--100 |
| 7.1 | 115--116 |
| 7.2 | 121--122 |

渲染证据：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P03-R1_VISUAL\page_*.png`。

视觉结论：`PASS`。

- 题干、解答标题、七阶段标签与唯一结论均清晰可读。
- 跨页例题均有正确的“解答（续）”页眉或完整的题干/解答衔接。
- 无裁切、重叠、公式畸形、字符缺失、异常留白、断裂边框或不可接受分页。
- 页眉、页脚、册/章标题与导航链接区域正常。

## 冻结确认

构建、定位和视觉期间业务源码未变化；仍仅 V1-C01.tex 至 V1-C07.tex 七文件、82 insertions/48 deletions，`git diff --check` PASS。未重复运行输入未变的 9 项静态门。
