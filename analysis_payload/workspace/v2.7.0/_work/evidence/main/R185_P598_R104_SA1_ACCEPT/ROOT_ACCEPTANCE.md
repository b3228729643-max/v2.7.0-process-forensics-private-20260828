# FIG-P598-01 R104 fresh SA1 中央接受

- Revision：185
- 中央裁决：`ROOT_ACCEPT_SA1_PASS_TO_FRESH_ISOLATED_SA3`
- UID：`FIG-P598-01`（B49）
- identity：`A-R104-P598-01-SA1-FRESH-20260825`
- 官方候选：R104，物理页 649
- 官方 PDF：817 页，4,967,222 bytes，SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- evidence root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-01\STRICT_R1_SA1_FRESH_R104_R168_20260825`

## 中央复核结论

- 独立分母 142 glyph + 22 visible graphic=`N164`，另有4条白色双圈辅助遮挡路径单列裁决；完整 unordered pairs=`13,366`。
- empty mask/tofu/低于数值硬门/illegal overlap/clip 均0；17个原始交叠全是箭线、箭头、节点等预期结构连接。最小crop-edge clearance 9px。
- 17个critical clearance、17个raw relationship、6个endpoint均有逐项overlay；最后两箭头core-mask间隙1.8284/2.6056px在原生栅格中有明确抗锯齿连接，不是肉眼断边。
- 语义精确为`t=0,1,2,3,4,5,T`上的`a,b,b,c,c,b,a`，六条相邻转移、等间距时间轴、`K(x_t,d x_{t+1})`、双圈重复状态和相邻相关解释均正确。
- R168字体门：无缺字/tofu、错码、数学语义错、实际不可读、严重肉眼失衡、真实裁切或碰撞；字号、旧taxonomy与细微栅格差只作advisory。
- 主线实际打开整页、彩色/灰度裁图、语义overlay、关系矩阵、glyph contact、critical clearance与末箭头endpoint；页面融合、题注和全部关系视觉PASS。

## 封存机械门

- root files 278；root payload 275；manifest entries 277=`275 evidence + external report + external handoff`，另自排除双manifest与`WRITE_STOPPED`。
- JSON manifest path/bytes/SHA mismatch0；SHA manifest 277/277 mismatch0；ADS0、只读失败0。
- `WRITE_STOPPED`严格晚于全部前置文件11,270,019 ticks，封后写0。
- JSON manifest SHA-256=`F1909145C71705A52949D7688609841F3CF8F0BB0A0B3B1789C7C5DA493D96F2`
- SHA manifest SHA-256=`8C239450F871ACC13265C586629C5FCC8207CD2539427A006AF5C0C3E870D22C`
- marker SHA-256=`418112239CE49035A96CB2F643D94AA6A12DDF1554077EEFF2BFA4A3B2A71824`

## 路由

本轮只接受 SA1 PASS，不计 local pass。A须以同一角色槽启动不同的、`fork_turns=none` 的 R104 fresh isolated SA3，绝对禁读本SA1 evidence/report/handoff及全部旧P598角色证据与结论；白名单只保留R104 PDF、当前P598单源、Goal/protocol/schema与必要当前相邻正文。TeX和业务源写入继续禁用。
