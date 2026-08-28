# FIG-P638-01 R104 fresh isolated SA1 中央验收

- Revision：201
- identity：`C-FIG-P638-01-R104-SA1-FRESH-ISOLATED-V1`
- 实例：`/root/sa1_fig_p638_r104_fresh_isolated`
- 官方页映射：R104物理688 / 印刷675 / 图33.5
- 裁决：`ACCEPT / SA1_PASS_REQUEST_FRESH_SA3`

## 机械与证据边界

- sealed manifest 58项，actual ordinary=60，extra仅`SEALED_MANIFEST.csv`与`WRITE_STOPPED`；逐项path、bytes、SHA-256与NTFS FILETIME复算差0。
- 60/60文件只读；ADS、pyc、cache与封后写入均为0；`WRITE_STOPPED`严格最新425,864,682 ticks。
- 独立分母：16 objects（10 text/formula + 6 graphic），C(16,2)=120；202 visible glyphs，C(202,2)=20,301；critical object pairs=21。
- manual glyph/object/all-object-pair/critical分母分别202/16/120/21；非PASS与空note均0。人工note唯一数分别38/16/119/21，且测量脚本不创建或改写manual文件。
- 唯一raw候选为E003/E004 vector bbox重叠产生的17个重复选择像素；原生墨迹结束/开始行1085/1092，中间六个空行，隔离mask交集0、净距8px，故为`MASK_CONTAMINATION_CONFIRMED`。装饰分隔线与两条警示箭头各2px为有意结构交叉；canonical illegal overlap=0、clip=0。

## 中央视觉与语义

主线打开R104整页、300dpi彩色与灰度裁图、object overlay、上方流程8x与下方例外框8x证据。精确满条件提议、MH比值逐项抵消、`alpha=1`与直接接受，以及近似/其他提议恢复MH接受率并保留拒绝自环的上下逻辑清楚；公式、箭头、边框、caption和相邻正文一致。9.2pt与自然script的旧微阈值差异在R168下仅为advisory，未出现缺字、错码、不可读、明显失衡、裁切或非法重叠。

## 迁移

- `FIG-P638-01`：SA1 → 完全fresh isolated R104 SA3；不计local pass。
- inventory：`35 SA1 / 53 SA2 / 1 SA3 / 10 A_LOCAL_PASS`；严格最终仍为`0/99`。
- C继续P610现有fresh SA1，并以释放的第二槽启动P638 fresh SA3；不启第三角色、TeX或源码写者。

