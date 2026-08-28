# R194｜FIG-P605-01 R104 fresh isolated SA1 中央接收

- 中央裁决：`ACCEPT_SA1_PASS_TO_FRESH_ISOLATED_SA3`
- HANDOFF_ID：`C-FIG-P605-01-R104-SA1-FRESH-ISOLATED-V1`
- 证据根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P605-01\sa1_r104_fresh_isolated_v1`
- 官方候选：R104，817页A4，4,967,222 bytes，SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- 定位：物理页658、印刷页645、图32.7。

## 一次性中央机械验收

- `MANIFEST.csv`列出465项；sealed root普通文件467=`payload 465 + MANIFEST.csv + WRITE_STOPPED`。逐项path、bytes、SHA-256、NTFS FILETIME与文件系统复算差异0，missing/extra 0。
- 467/467只读；ADS、pyc、`__pycache__`均0；`WRITE_STOPPED`严格最新且封后写入0。
- 独立分母：150 visible glyph；N32=15 text+17 graphic；完整无序pair 496/496；critical ROI 14。
- manual glyph/object/pair分别150/32/496，ID与分母闭合；pair分类为484 clear、10 design connection、2 mask contamination，raw/design/contamination/illegal像素为86/80/6/0。机器脚本不生成默认或批量人工PASS。
- clip、empty mask、真实illegal overlap、硬clearance失败均0；23个PDF figure drawing全部映射，unmapped 0。

## 中央视觉与语义验收

- 已打开整页、300dpi彩色裁图、灰度、完整对象overlay、代表glyph sheet及设计连接/颜色mask污染关键ROI。
- 左侧固定顺序复合 `K_sys=K_1 K_2 ... K_d` 与“通常不保证可逆”限定正确；右侧 `J~omega`、三分支坐标选择和 `K_rand=sum_{j=1}^d omega_j K_j` 正确。
- 各坐标核关于pi可逆时，固定权重混合保持可逆的表述、连线方向、节点、题注与源码一致。
- 9.2pt/自然脚本/短运算符等旧微观门仅为R168 advisory；所有内容完整、码点正确、清晰可读、无明显失衡或裁切。

## 路由

P605由SA1迁入SA3；启动另一完全fresh、fork_turns=none的R104隔离SA3，使用启动前不存在的新根，绝对禁读本SA1 evidence/report/result与所有旧P605结论。当前不计C_LOCAL_PASS或全局PASS，不授权TeX或源码写入。C同时仅保留P603与P605两条SA3，不启动第三角色。
