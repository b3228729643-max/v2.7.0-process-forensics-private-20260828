# R192｜FIG-P603-01 R104 fresh SA1 中央接收

- 中央裁决：`ACCEPT_SA1_PASS_TO_FRESH_ISOLATED_SA3`
- HANDOFF_ID：`C-FIG-P603-01-R104-SA1-FRESH-ISOLATED-V1`
- 实例：`/root/sa1_fig_p603_r104_fresh_isolated`
- 证据根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P603-01\sa1_r104_fresh_isolated_v1`
- 官方候选：R104，817页A4，4,967,222 bytes，SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- 定位：物理页655、印刷页642、图32.6。

## 一次性中央机械验收

- sealed root 普通文件638=`manifest 636 + MANIFEST.json + WRITE_STOPPED`；manifest path、bytes、SHA-256、NTFS FILETIME与文件系统逐项复算差异0，missing/extra 0。
- 638/638只读；ADS、pyc、`__pycache__`均0；`WRITE_STOPPED`严格最新且封后写入0。
- 独立对象分母N24=11 text+13 foreground graphic；完整无序pair为276/276；glyph为150；critical为23。
- manual ledger分母闭合：glyph150、object24、pair276、role11、content9、hard13、view28。ID唯一，空ID/空note/重复模板note均0；终检脚本只读现成人工账，不生成或批量填充人工字段。
- illegal overlap、clip、empty mask、below-clearance、missing/foreign glyph pixel均为0；11个原始几何交叠均为坐标轴、刻度、箭头、曲线或折点的设计连接。

## 中央视觉与语义验收

- 已打开整页、300dpi彩色裁图、灰度、对象overlay、代表性glyph sheet、critical-pair sheet及公式分数线证据。
- 曲线严格表达 `alpha=min{1,r}`：`r<1`段为上升直线、`r>=1`段为平台1；折点、虚线辅助、坐标轴和标注关系一致。
- 一般比值 `r=pi(y)q(y,x)/[pi(x)q(x,y)]` 及独立提议特例 `r=w(y)/w(x)` 的分子分母和参数方向正确；题注与相邻正文一致。
- 五个等号的旧像素高度、8.5/9.2pt声明及四个无exact-peer标点按R168仅为advisory；全部字形完整、编码正确、清晰可读且无明显失衡，不构成硬失败。

## 路由

P603由SA1迁入SA3；必须启动另一完全fresh、fork_turns=none的R104隔离SA3，绝对禁读本SA1根、报告、结果卡及任何旧P603证据/结论。当前不计C_LOCAL_PASS或全局PASS，不授权TeX或源码写入。
