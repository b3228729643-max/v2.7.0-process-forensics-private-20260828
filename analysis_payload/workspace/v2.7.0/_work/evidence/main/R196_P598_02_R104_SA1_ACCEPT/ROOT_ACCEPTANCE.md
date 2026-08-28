# R196｜FIG-P598-02 R104 fresh isolated SA1 中央接收

- 中央裁决：`ACCEPT_SA1_PASS_TO_FRESH_ISOLATED_SA3`
- HANDOFF_ID：`A-R104-P598-02-SA1-FRESH-20260826`
- 证据根：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-02\STRICT_R1_SA1_FRESH_R104_R168_20260826`
- 官方候选：R104，817页A4，4,967,222 bytes，SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- 定位：物理页650、印刷页637、图32.3。

## 一次性中央机械验收

- 双manifest声明并列出325项payload；sealed root普通文件329=`payload 325 + MANIFEST.json + MANIFEST.sha256 + SEAL.json + WRITE_STOPPED`。逐项path、bytes、SHA-256与文件系统复算差异0，extra恰为四个控制文件。
- `MANIFEST.json` SHA-256=`EE0DF14C4722B06F44A8F5B9511FF3CCA7748B33E4C7C75C0A2668721C235E74`；`MANIFEST.sha256` SHA-256=`D657510E04AE08563229B92356F412164CAFE02337D6A887645395F9B194A580`，与`SEAL.json`一致。
- 329/329普通文件只读；非默认ADS=0；`WRITE_STOPPED`严格最新727,160 ticks；pyc/cache与封后写入均0。
- 独立分母：137 glyph + 26 graphic = N163；完整无序pair 13,203/13,203；critical relationship 22/22；machine pair FAIL、empty mask、clip、final-visible illegal overlap均0。
- manual glyph/graphic/relationship/view/role-script/font-hard/semantic分别137/26/22/15/24/6/13，ID分母闭合、空ID/空note/非PASS均0；role-script用`panel|role|script_or_class`复合键24/24唯一。

## 中央视觉与语义验收

- 已打开R104物理页650整页、300dpi彩色与灰度standalone、semantic overlay、完整163×163 pair矩阵、代表glyph/graphic contact及critical overlay。
- 三张有序卡片、两条流程箭头、`pi K = pi`、x/y双向核、warm-up阴影弃置区与保留段、保留样本点、遍历平均公式及题注`E_pi[h(X)]`语义均完整一致。
- 无缺字/tofu、错码或数学含义错误；图形、边框、箭头、虚线、宽帽、分数线和文字均清楚，无真实裁切、非法重叠或明显失衡。旧细粒度字号/像素门按R168仅作advisory，不构成硬FAIL。

## 路由

FIG-P598-02由SA1迁入另一完全fresh、fork_turns=none的R104隔离SA3。新SA3必须使用启动前不存在的新根，绝对禁读本SA1 evidence/report/handoff/result与全部旧P598-02/P598-01结论；PDF、源码与主线只读，TeX禁用。当前不计A_LOCAL_PASS或全局PASS。
