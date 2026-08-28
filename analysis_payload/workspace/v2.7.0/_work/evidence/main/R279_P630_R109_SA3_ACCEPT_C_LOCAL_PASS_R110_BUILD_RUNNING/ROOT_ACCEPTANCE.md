# Revision 279 — P630 R109 fresh SA3 接受为 C_LOCAL_PASS

时间：2026-08-27T01:08:49+08:00  
主线：`v2.7.0/integration` / `aa7eb7c4fcf0f702e3e485330c9e02a8304501d6`  
官方审查候选：R109，817页，4,967,054 bytes，SHA-256 `936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9`

## 接受的 fresh SA3

- HANDOFF_ID=`C-FIG-P630-01-R109-SA3-FRESH-ISOLATED-V1`。
- actual instance=`/root/sa3_fig_p630_r109_fresh_isolated_v1`；`gpt-5.6-sol/xhigh`；`fork_turns=none`。
- sealed root=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P630-01\sa3_r109_fresh_isolated_v1`。
- 独立定位 physical680 / printed667 / Fig33.1；语义对象 `N=17`，全部 unordered pairs `C=136`，另有 26 个文字/公式元素与 10 个关键 native1x/nearest8x ROI。
- 机器/人工：17/17 objects、136/136 pairs、26/26 text rows、10/10 ROI 全覆盖；true overlap0、clip0、hard failure0、unresolved0，最小文字净距4px。六节点有向链、两侧说明、公式、题注、灰度与页面融合均PASS；1px字形微差仅按R168记advisory。

## 跨角色分母裁决

- 已接受SA1使用较细粒度 `N=36/C=630`：9个节点边框、5条主箭头、2条leader、20块文字/题注分别作为对象。
- fresh SA3使用 `N=17/C=136`：9个节点/题注复合语义对象、5条主箭头、2条leader与题注作为对象，并在独立 `26/26` 文字/公式表中逐项复核内容、字号、像素与净距。
- 两种对象粒度都覆盖完整图面；SA3没有借降低N省略文字、公式、边框或题注。分母差异接受为独立建模差异，不构成证据缺口。

## 主线机械与视觉复核

- ordinary=27；manifest rows=25；expected payload=25；duplicate/missing/extra/path-bytes-SHA mismatch均0。
- 27/27文件与root目录只读；ADS/cache/pyc/reparse=0。
- `WRITE_STOPPED` ticks=`639233602978327665`，严格晚于其余最大 `639233602882087005`，margin=`96,240,660` ticks；files at/after marker=0。
- report SHA=`8FBEACE70A52A37C29ECF51D0C837B3770CAFC7E0DB907E79A5C71AD93BA9F24`；handoff SHA=`C97E692D3B160C771367DCC2D69D79555A70C9EAA80E5710E66355D27BC19D3C`；manifest SHA=`ADE84C9EBC2CD03F0B0220BC8BA98CB1500D22DD8A406F2BCC486276B70425BF`；WSTOP SHA=`00C513CB40CB450D6341A4B20F156332B4B3E0F3003E9422DA76B96BBBD44F72`。
- 主线实际打开 native300dpi figure+caption、semantic object overlay、text measurement overlay 与 critical nearest8x sheet；节点、箭头、leader、公式、`≠`、题注均完整清晰，无碰撞、裁切、错位、缺字或不可读反证。

## 裁决与资源

- 正式裁决：`P630_R109_C_LOCAL_PASS_ACCEPTED`。P630源码、R109角色证据与handoff永久冻结，不重复角色。
- inventory：`31 SA1 / 47 SA2 / 0 SA3 / 21 local pass`；严格最终仍为 `0/99`，不得把local pass冒充全书最终。
- R110全书唯一父构建仍在同一已授权链运行；本验收未启动、终止或管理任何TeX进程。R110冻结后再路由P582 fresh SA1与C域下一UID。
