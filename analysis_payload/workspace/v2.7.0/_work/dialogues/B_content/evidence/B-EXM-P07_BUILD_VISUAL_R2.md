# B-EXM-P07 R2 root 机械与视觉终检

- 批次：`B-EXM-P07`
- 轮次：`R2`
- root 结论：`MECHANICAL_PASS / VISUAL_PASS`
- R1 历史：物理页719两段极端竖直胶伸展，`VISUAL_FAIL`；不得复用 R1 的视觉结论。

## 唯一构建身份

- 工作流：一个 `run_background_build.ps1 -Resume` 父 invocation 及其自然内部 LuaLaTeX 遍次；无并发、retry 或 R3。
- CONTROL：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P07-R2-CONTROL`
- OUTPUT：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P07-R2-RESUME`
- started：`2026-08-25T10:56:51.6629361+08:00`
- finished：`2026-08-25T11:10:53.6939021+08:00`
- wrapper / child exit：`0 / 0`
- PDF：`main_full.pdf`，817 页，A4 `595.276 x 841.89 pt`，rotation 0，PDF 1.7，未加密，`4,958,381 bytes`
- log：`main_full.log`，`249,757 bytes`
- 最终输出行：`Output written on main_full.pdf (817 pages, 4958381 bytes).`
- 构建结束后 `latexmk/lualatex/luatex/luahbtex=NONE`；主线已确认锁收回。

## 机械门

- 817/817 页均为 A4。
- undefined control、LaTeX/package error、fatal/emergency、missing I/O、memory、undefined refs/citations、final rerun、multiply-defined、missing chars：均为 0。
- overfull/underfull hbox/vbox：均为 0。
- 主索引：731 accepted、0 rejected、0 warnings。
- 符号索引：355 accepted、0 rejected、0 warnings。
- stderr 仅含已知 Perl locale fallback、首遍缺少 toc/ind 的自然提示与 makeindex 正常输出；最终遍次全部闭合。

## R2 新 AUX 十目标定位

| 对象 | 印刷页 | 物理页 |
|---|---:|---:|
| 33.1 | 669 | 682 |
| 34.1 | 704 | 717 |
| 34.2 | 707 | 720 |
| 34.3 | 708 | 721 |
| 34.4 | 709 | 722 |
| 35.1 | 738 | 751 |
| 35.2 | 739 | 752 |
| 35.3 | 740 | 753 |
| 36.1 | 764 | 777 |
| 36.2 | 765 | 778 |

## 视觉覆盖

- 以 Poppler 150 dpi 重绘并逐页打开 23 页：物理页 `681--684`、`716--724`、`750--754`、`776--780`。
- 图片根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P07-R2_VISUAL`。
- 物理页718--721逐页重点复核：
  - 718：例34.1解答续页与算法前说明完整，无断框。
  - 719：仅保留一个“读前自检：闭式更新与后验预测”段落，紧接算法34.1；R1的两段极端空白完全消失，算法内容完整、无裁切或拥挤。
  - 720：算法相邻说明与例34.2自然衔接，无回归。
  - 721：例34.2续页及例34.3完整，无裁切、重叠或异常间距。
- 其余19页覆盖十目标与前后相邻内容；无裁切、重叠、断框、公式溢出、孤立标题、异常伸展或分页回归。
- 视觉计数：`23/23 PASS`。

## R2 语义与结构保持

- `KN-V5-C34-ALGORITHM_IDEA-001=1`、`KN-V5-C34-ALGORITHM_IDEA-002=1`。
- “读前自检：闭式更新与后验预测”主题段=1；输入、合法条件、原子提交和停止证书语义完整。
- P07 checker 10 targets、70/70、10/10 labels/headings、环境栈 PASS；9 tests OK；累计业务差异4文件71+/82-，staged0，`git diff --check` PASS。

## 后续边界

root 机械与视觉已 PASS，但尚未启动任何 fresh SA1/SA3、尚未提交、尚未进入 P08。等待主线接受本报告并明确路由后继续；TeX保持禁用。
