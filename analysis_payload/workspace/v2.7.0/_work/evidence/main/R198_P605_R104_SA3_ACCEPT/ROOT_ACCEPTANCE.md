# R198｜FIG-P605-01 R104 fresh isolated SA3 中央接收

- 中央裁决：`ACCEPT_SA3_PASS_AS_NINTH_LOCAL_PASS`
- HANDOFF_ID：`C-FIG-P605-01-R104-SA3-FRESH-ISOLATED-V1`
- 证据根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P605-01\sa3_r104_fresh_isolated_v1`
- 官方候选：R104，817页A4，4,967,222 bytes，SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- 定位：物理页658、印刷页645、图32.7。

## 一次性中央机械验收

- `MANIFEST.csv`列出661项；sealed root普通文件663=`payload 661 + MANIFEST.csv + WRITE_STOPPED`。逐项resolved path、bytes、SHA-256、NTFS FILETIME与文件系统复算差异0，extra恰为manifest与marker。
- 661项payload与`MANIFEST.csv`全部只读；非默认ADS=0，pyc/cache=0；`WRITE_STOPPED`严格最新1,073,194,260 ticks。marker按C封存声明排除在`CONTENT_READ_ONLY`边界之外且自身为Archive，不误写为全根只读。
- 独立分母：150 glyph + 23 graphic = N173；完整无序pair 14,878/14,878；13个raw intersection candidate合计224px，人工裁为4个同公式内部接缝与9个结构端点/箭颈连接；mask contamination、illegal overlap、clip、empty mask均0。
- manual glyph/graphic/candidate-pair/hard/role-peer/semantic/source-font/view分别150/23/13/24/15/26/9/20。对象、pair、role复合键与view分母闭合；空ID/空note0；终检脚本只读取人工账，`manual_decisions_generated_or_overwritten=false`。
- `FINAL_MACHINE_CHECK.json` 38/38 PASS；TeX=`DISABLED`，source-writer=`NONE`，中央state/inventory未由支线写入。

## 中央视觉、语义与分母裁决

- 已打开整页、300dpi彩色裁图、灰度、measurement overlay、代表glyph/graphic contacts及首尾raw candidate 8x ROI。
- 左侧固定顺序复合`K_sys=K_1K_2...K_d`与“通常不保证可逆”限定正确；右侧`J~omega`、三坐标分支、`K_rand=sum omega_jK_j`及“各K_j关于pi可逆则固定权重混合保持可逆”正确。节点、连线、箭头、题注与正文一致。
- SA1 N32采用15 text parent+17 graphic parent并另审150 glyph；SA3把150 glyph直接纳入N并以23个PDF drawing前景对象保守细分，完整14,878 pair和13个接触候选均覆盖。差异为粒度扩张，不是候选漂移或漏对象。
- 9.2pt、自然脚本与低轮廓符号仅作R168 advisory；未见缺字/tofu、错码、数学语义错误、真实不可读、明显失衡、裁切或非法重叠。

## 路由

FIG-P605-01计入共享第9个local pass。其SA1/SA3根保持不可变，不再启动该UID角色。C侧已释放两条角色槽，可按C独占清单启动下一两个互不冲突、完全fresh、只读、禁TeX的R104 SA1；不得启动业务图源写者。
