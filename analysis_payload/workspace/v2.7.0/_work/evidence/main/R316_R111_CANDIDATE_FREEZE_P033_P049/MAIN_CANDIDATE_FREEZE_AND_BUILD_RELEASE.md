# R316 — R111 正式候选冻结、构建锁释放与 P033/P049 定位

- 主线 HEAD：`b819e9f4810a2afc04d24a2f0b8bdaa2a3ccb079`；工作树与 index 均 clean。
- 唯一父调用：`build_v2.7.0.ps1 -Engine lualatex -OutputDir src/build/strict_current_r111_fullbook -NoPublish`。
- 结果：父调用自然 `exit 0`，wrapper `result=PASS`；无第二父调用、无人工 retry、无 Resume、无中止。
- 同一 latexmk 父链内部自然完成 3 次 LuaLaTeX 收敛与索引生成：首遍临时 802 页，第二遍 817 页，第三遍稳定 817 页；`main_full.ind` 与 `symbols.ind` 均由 makeindex 正常生成。
- 正式 PDF：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf`
- PDF 身份：4,967,076 bytes；SHA-256 `DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6`；817 页；A4 `595.276 × 841.890 pt`；PDF 1.7；未加密；旋转 0。
- 最终日志门：LaTeX error、fatal/emergency、undefined control sequence、undefined reference、需重跑交叉引用信号均 0；`main_full.toc` 118,583 bytes、`main_full.ind` 23,734 bytes、`symbols.ind` 25,820 bytes。
- 导航门：PDF outline 273 项，链接 4,961 个；首页尺寸与 A4 一致。
- 终态资源门：`latexmk/lualatex/luatex/luahbtex=NONE`。因此 R111 构建锁已正式释放。

## 目标图官方定位与代表性视觉核对

- `FIG-P033-01`：R111 physical 29 / printed 16 / Fig 2.1；当前源 SHA-256 `D3C1D38ECB8468EC3294F7D18BD886316829F14690A516000189CE853A07BC05`。
  - 已实际打开 200dpi 整页与 native300dpi 图体+题注裁切。
  - “子空间 S”标签与下侧子空间边界保持清楚可见白隙；未见裁切、非法重叠、错码或页面融合反证。
- `FIG-P049-01`：R111 physical 48 / printed 35 / Fig 3.1；当前源 SHA-256 `27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E`。
  - 已实际打开 200dpi 整页与 native300dpi 图体+题注裁切。
  - Guide1 从说明1路由至外层 `c3`，与 Guide2/3、梯度、切线、直角标记及文字保持视觉分离；未见裁切、非法重叠、错位或页面融合反证。

本门仅冻结 R111 官方候选身份与代表性页面方向，不替代后续 completely fresh isolated SA1/SA3 全分母审查。P641 已启动的 R110 fresh SA3 保持其冻结输入直至封存；不得迁移到 R111 或重启角色。
