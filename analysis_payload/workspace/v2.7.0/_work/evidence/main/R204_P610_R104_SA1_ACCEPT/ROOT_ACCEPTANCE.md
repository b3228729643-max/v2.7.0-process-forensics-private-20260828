# FIG-P610-01 R104 fresh isolated SA1 中央验收

- Revision：204
- identity：`C-FIG-P610-01-R104-SA1-FRESH-ISOLATED-V1`
- 实例：`/root/sa1_fig_p610_r104_fresh_isolated`
- 官方候选：R104物理662 / 印刷649 / 图32.10；817页A4，4,967,222 bytes，SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- 裁决：`ACCEPT / SA1_PASS_REQUEST_FRESH_ISOLATED_SA3`

## 机械与证据验收

- 当前单源SHA-256=`3E3B5CB5604EB0945F77850B1350ABD946FA592D78AF0983AB04EDDACB5D84EE`，source writer与TeX均为NONE。
- manifest545 / actual547，extra仅`MANIFEST.csv`与`WRITE_STOPPED`；逐项resolved path、bytes、SHA-256与NTFS FILETIME复算差0。545 payload与manifest全只读；marker按C seal contract排除内容只读边界且自身Archive。ADS/cache/pyc/postseal0，marker严格最新5,786,984 ticks。
- 独立分母：18 text parents + 22 graphic foreground = N40，C(40,2)=780；glyph132；critical pairs11；24/24 PDF drawing refs映射、unmapped0。
- manual glyph/pair=132/780，复合ID唯一、空note0、逐项note唯一132/780；机器脚本不生成/改写人工账，seal脚本只读并核对manual集合和机器量测。
- raw overlap/overlap pixels/clip/edge contact均0；最小critical真实间距5px，figure-crop边缘最小11px。

## 中央视觉与语义验收

主线打开整页、300dpi彩色与灰度裁图、对象overlay、代表glyph contact、完整pair contact页及最小5px的PAIR-0748 8x。左图Y1/Y2/Y3中拒绝Y2后输出Y1/Y3并留空；右图拒绝Y2后以双圈重复当前Y1，再到Y3，输出Y1/Y1/Y3。节点、双圈、箭头、拒绝叉、说明、caption与相邻正文一致；未见缺字/错码、不可读、明显失衡、裁切或非法重叠。低轮廓标点与5px间距仅为R168 advisory。

## 迁移

- `FIG-P610-01`：SA1 → 完全fresh isolated R104 SA3；不计local pass。
- inventory：`35 SA1 / 52 SA2 / 2 SA3 / 10 A_LOCAL_PASS`；严格最终仍`0/99`。
- C继续P638现有fresh SA3，并用P610释放的同一槽启动唯一P610 fresh SA3；不得启动第三角色、TeX或源码写者。

