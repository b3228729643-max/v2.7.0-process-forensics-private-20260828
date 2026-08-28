# FIG-P598-02 R104 fresh isolated SA3 中央验收

- Revision：200
- UID：`FIG-P598-02`
- HANDOFF_ID：`A-R104-P598-02-SA3-FRESH-ISOLATED-20260826`
- 官方候选：R104，物理页 650，817 页 A4，4,967,222 bytes，SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- 中央裁决：`ACCEPT / A_LOCAL_PASS`

## 机械验收

- SA3 从零分母与已接受 SA1 完全一致：137 glyph + 26 graphic = N163，全部无序 pair `C(163,2)=13,203`。
- 双 manifest 均为 238 项；CSV/JSON 对同一载荷的 path、bytes、SHA-256 交叉复算差异为 0。CSV SHA-256=`3E76EEFE3E9DE4AF22EA48854888EF6CC22EF107C404EF873AD3B1313F0C0362`；JSON SHA-256=`C8644E555E5E5A9BB38002B8CC98947EB1E645059EA8DED0280D582F4C4E6B49`。
- evidence root 内 ordinary=239：236 个根内载荷 + 两份 manifest + `WRITE_STOPPED`。manifest 另绑定根外正式 report 与 handoff；二者 bytes/SHA 复算一致。
- 根内 239/239 文件只读；ADS、pyc、`__pycache__` 与封存后写入均为 0。`WRITE_STOPPED` 严格晚于其余根内文件 603,314 ticks。
- 人工账：objects 163/163、relationships 16/16、views 8/8，ID 唯一、空 note 与非 PASS 均为 0。对象 note 中存在同类真实观察短语，但每项均绑定唯一 object ID、sheet、cell、observation order 与 reviewer；终检脚本只读人工账，不生成或批量覆盖结论。
- machine final check 全部为 true；13,203 pair 的非法交叠像素为 0，clip、empty、duplicate、hard-clearance 与 R168 真实字体硬失败均为 0。

## 中央视觉与语义验收

主线一次性打开并核对 SA3 自身的整页、300 dpi 彩色/灰度裁图、全对象 overlay、glyph/graphic contact、代表性 critical relationship ROI 与完整 pair matrix。三张有序卡片、两条流程箭头、`\pi K=\pi`、warm-up 舍弃/保留样本、遍历平均公式、链轨迹与题注语义均清楚一致；未见缺字、错码、不可读、真实非法重叠、裁切或页面融合回归。

## 迁移

- `FIG-P598-02`：SA3 → `A_LOCAL_PASS`。
- 全局分布：`36 SA1 / 53 SA2 / 0 SA3 / 10 A_LOCAL_PASS`。
- 这是共享第 10 个 local pass；严格最终仍为 `0/99`，不声明全书完成。
- P598-02 的源码、证据与 handoff 立即冻结；R104继续是唯一官方候选，不触发 TeX 或源码写者。

