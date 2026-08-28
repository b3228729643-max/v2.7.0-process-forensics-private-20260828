# R381：P665 R113 readonly SA2 接受与 fresh SA1 授权

时间：2026-08-27T18:32:05+08:00

## 主线裁决

主线独立接受 `C-FIG-P665-01-R113-SA2-R168-READONLY-ADJUDICATION-V1` 为：

`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

不修改 P665 source，不启动 TeX/build，不计 C_LOCAL/global/final pass。原 SA2 root、报告、台账、图像和 controls 永久冻结。

## 冻结输入与定位

- official R113：4,967,121 bytes，SHA-256 `6B48D215721463EA2A9B94EFA54200F8D767B609E47714A70D9B441328F2BB9D`。
- current P665 source：2,800 bytes，SHA-256 `65F9C440D3058569C920F8C2E7E7B50545241EDAA6B6DAD4AA27EEF858324E6B`。
- main HEAD：`3bc644256d833272a789a7685b91996f98fa3336`，worktree clean；终态 TeX 四类进程0。
- fresh 独立定位：R113 physical713 / printed700 / Fig34.6。

## sealed root 独立机械验收

Root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa2_r113_r168_readonly_adjudication_v1`

- `SEALED_MANIFEST.csv` 44 rows，payload FS44；加 manifest 与 final marker 后 ordinary files46。
- duplicate/missing/extra/path/bytes/SHA/creation FILETIME/lastwrite FILETIME mismatch 全0。
- 46/46 files、6/6 directories including root 均 Windows ReadOnly。
- JSON/CSV parse failures0；ADS/cache-pyc/reparse0。
- `FINAL_MARKER.txt` 6 physical lines/6 unique required keys，HANDOFF_ID/UID/SEALED_ROOT/MANIFEST_ROWS=44/MANIFEST_SHA256/VERDICT 精确。
- marker FILETIME=`134322998540618631`，max other=`134322998520040086`，strict latest margin20,578,545 ticks；at-or-after excluding marker0。
- manifest SHA-256 `06B368CD950F073FABE330292B5F1CF4EF38EF66B0373EA331270B8C533188A3`；marker SHA-256 `1275EE6BD5D4B7E66EB172B3FF806EF595F54E17AF68AFB29167BF31037A41CF`。

冻结的 `machine/postseal_audit.ps1` 是便利审计脚本，角色已透明披露其 duplicate-key/marker-parser 逻辑缺陷。该脚本不是授权硬门，主线未依赖其输出；以上 set、identity、FILETIME、ReadOnly、hygiene 和 marker 结果均由 root-external 独立只读复算直接闭合，故该冻结脚本缺陷不否决实际 root 身份，也不授权修改或重封原根。

## 台账与业务验收

- denominator `N=16`，all unordered pairs `C=120`；machine/manual pair ID、object endpoints、bbox intersection/gap 对应零差。
- genuine manual：objects16/16、pairs120/120、text/glyph14/14、geometry12/12、views20/20、hard gates14/14、mathematics10/10、semantic/reading-order12/12。
- 所有必填字段非空、ID unique；machine tables 中 manual/reviewer/decision/note 字段数0。
- pair dispositions：111 clear、8 conservative-bbox contamination only、1 inline-caption relation；missing/extra/unresolved0。
- native hard defects：missing/tofu/wrong codepoint0、unreadable/serious imbalance0、clip0、illegal visible-ink overlap0、semantic/geometric/math error0。
- 8.5pt brace 与旧 pixel/ratio 数值门按 R168 仅 advisory；native1x/NN8x 显示完整、清楚、协调。
- 数学独立复算正确：`A(α)=log B(α)`，`∂A/∂α_k=ψ(α_k)−ψ(α_0)=E[log Θ_k]`；当前 K≥2、α_i>0 非退化语境下，严格 Jensen 给出 `E[log Θ_k] < log E[Θ_k]`，图中不等号与题注正确。

## 主线实际打开的代表性证据

- color native figure：173,872 bytes，SHA `8030933259DC5B4E5ED8D664F34EE71566CD4F98C3715854225C70052BA0E969`。
- grayscale native figure：81,541 bytes，SHA `7B62BEEFE997C4D89B6CBE4A1A3B387B9EF8BD1384DD763F0F1014658096ADF0`。
- semantic object overlay：185,607 bytes，SHA `8A4657041DDB26708AEAA4DD26D372A6971F9A2E52C5EEDEC2539808D89B2402`。
- page integration：244,397 bytes，SHA `6186AA80BD8917728244E1E9472CFDBFD70B8B44DE509AB74D36D51CD4852EDB`。
- density/brace native1x：SHA `0BAAC6D6B4A00F9E9DF2C7D5BEBFF7C9283237BA421E18DFE1110D799E8C7F61`；NN8x：SHA `22F907E7D82231F5FF104FA1B1A03CE00A08A36F1D594AFAE30586C2B048AFAD`。
- right derivative stack NN8x：SHA `5879AA7E5877E9A97FE5EE8B7510FF02403ED80D78997BBB9C49FE28AD5B0675`。
- caption native1x：SHA `0DB009E4624DDE31F4811EB7A03F5528385A7A8964E86D50F04B55A6E23E3C66`；panel gutter native1x：SHA `427B66E24144418824D21D014F1BE1C065ABB9FA7DDD5AAC297ECA98D62A89E1`。

主线观察无字体缺损、真实碰撞、裁切、灰度塌缩、panel 混读、题注断裂或页面融合反证。

## 唯一下一角色授权

C 获授权启动一个不同的 completely fresh isolated R113 P665 SA1：

- HANDOFF_ID：`C-FIG-P665-01-R113-SA1-FRESH-ISOLATED-V1`
- actual instance 预期：`/root/sa1_fig_p665_r113_fresh_isolated_v1`
- model/effort/fork_turns：`gpt-5.6-sol/xhigh/none`
- new root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa1_r113_fresh_isolated_v1`；主线授权前复核 file=false、directory=false、parent=true。

Fresh dispatch 只能含 official R113、main 当前 P665 单源、root GOAL/direct strict protocol-schema 与必要 current V5-C05 context。不得暴露或读取本 SA2 的页号、N/C、pair、metric、verdict、acceptance、root/evidence/report/handoff；绝对禁全部旧 P665、其他 UID、Main state/history/acceptance、Git/chat 结论及任何 agent/thread/task status/identity/history 工具。PDF/main/source 只读；TeX/build/source/Git/central/process management/second UID/second P665 role=0。

同一 fresh instance 从零直跑一次 sealed PASS/FAIL；PASS 仅请求另一个 different fresh isolated SA3，不得自计 C_LOCAL/global/final pass或自行启动 SA3。

P665 `SA2→SA1`；inventory 更新为 `33 SA1 / 37 SA2 / 0 SA3 / 30 local pass`。P067 R113 fresh SA1 同一实例继续，不受影响。

