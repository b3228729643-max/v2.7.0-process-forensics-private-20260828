# R248 P656 单源静态补丁接受与构建槽授权

- UID：`FIG-P656-01`
- 唯一源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_multinomial_counts.tex`
- 精确diff：1 file，5 insertions / 5 deletions；仅五个一般可见字号声明改为`9.5pt/11.4pt`。
- after identity：2,854 bytes；SHA-256 `9D404ED0694D575DE89038D3D6485C49AA4C60DCC3238AD8318CADACF810B381`。
- 静态门：六个fontsize声明最小9.5pt，低于9.5pt=0；resize/scalebox/transform=0；`git diff --check` PASS。
- 禁改域：文字、公式、坐标、节点尺寸、边、颜色、题注、语义均未变。
- 资源预检：授权前latexmk/lualatex/luatex/luahbtex=NONE；P020 fresh SA3仅只读、不启TeX。
- 授权：C先冻结上述static identity，再按既定流程仅一次P656本地图源LuaLaTeX；全新证据根和独立texcache；禁并发、自动retry和第二invocation。自然结束无论成败立即释放槽并回完整进程/PDF/source/wrapper身份。
- 构建后限制：只允许非TeX全量证据；未经新授权禁止commit、fresh role、第二UID。

记录时间：2026-08-26T17:32:55+08:00。
