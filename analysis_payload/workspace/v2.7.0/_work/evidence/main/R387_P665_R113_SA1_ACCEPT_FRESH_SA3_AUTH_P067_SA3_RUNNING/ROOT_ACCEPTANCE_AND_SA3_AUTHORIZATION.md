# R387：P665 R113 fresh SA1 接受与 fresh SA3 授权

时间：2026-08-27T18:58:21+08:00

## 主线裁决

主线独立接受 `C-FIG-P665-01-R113-SA1-FRESH-ISOLATED-V1` 为：

`SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

不修改 P665 source，不启动 TeX/build，不计 C_LOCAL/global/final pass。SA1 root、报告、handoff、台账、图像和 controls 永久冻结。

## 冻结输入与定位

- official R113：817 pages，4,967,121 bytes，SHA-256 `6B48D215721463EA2A9B94EFA54200F8D767B609E47714A70D9B441328F2BB9D`。
- current P665 source `fig_v5_c05_exponential_family_moments.tex`：2,800 bytes，SHA-256 `65F9C440D3058569C920F8C2E7E7B50545241EDAA6B6DAD4AA27EEF858324E6B`。
- main HEAD `3bc644256d833272a789a7685b91996f98fa3336`、C worktree HEAD `211bd3959e93379766184e8a07354c81df8536d4`；两者worktree/index clean。
- fresh 独立定位：R113 physical713 / printed700 / Fig34.6。

## sealed root 独立机械验收

Root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa1_r113_fresh_isolated_v1`

- `manifest.csv` rows38，payload FS38；加manifest与`FINAL.seal`后ordinary files40。
- duplicate/missing/extra/path/bytes/SHA/creation FILETIME/lastwrite FILETIME mismatch全0。
- 40/40 files、1/1 directory including root均Windows ReadOnly。
- CSV parse failures0；20 PNG signature failures0；ADS/cache-pyc/reparse0。
- `FINAL.seal` count1，6 physical lines/6 unique required keys，bad/duplicate/empty0；HANDOFF_ID/UID/SEALED_ROOT/MANIFEST_ROWS=38/MANIFEST_SHA256/VERDICT精确。
- marker FILETIME=`134323014443129244`，max other=`134323013814753697`，strict latest margin628,375,547 ticks；at-or-after excluding marker0，postmarker0。
- manifest SHA-256 `CA06811E02CA908D9098007CF346387F7AA6A4059106678945FD8E5D6AC75E37`。

## 台账与业务验收

- denominator `N=14` including caption；all unordered pairs `C=91=C(14,2)`。
- machine/manual object ID set14/14、pair tuple set91/91、text/glyph ID set16/16均exact；missing/extra/duplicate/self0。
- genuine manual：objects14 CLEAR；pairs86 CLEAR+5 NEAR_BUT_CLEAR；text/glyph16 CLEAR；geometry7 CLEAR；mathematics8 CORRECT；semantic/reading-order9 COHERENT；hard gates7 CLEAR+3 ADVISORY_ONLY；views20 CLEAR。所有必填字段非空，view file missing0。
- 五个NEAR_BUT_CLEAR为brace cusp、formula/arrow、arrow/derivative、derivative/card top、warning card/caption的保守bbox近距；native1x/NN8x均有真实白隙，无visible-ink collision。
- hard defects：missing/tofu/wrong codepoint0、实际不可读/严重失衡0、clip0、illegal visible-ink overlap0、semantic/geometric/math error0、unresolved0。
- 三项R168 advisory仅为T09 8.5pt与常见9.2pt旧数值门、近距bbox、base-measure中英术语风格；当前native可读性和语义均不受损。
- 数学独立闭合：Dirichlet指数族分解的`h(θ)`、`η_k=α_k−1`、`T_k(θ)=log θ_k`；`A(α)=log B(α)`；`∂A/∂α_k=ψ(α_k)−ψ(α_0)=E[log Θ_k]`；K≥2、α_j>0非退化条件下严格Jensen给出`E log Θ_k < log E Θ_k`，图中不等式正确。

## 主线实际打开的代表性证据

- subject native300：149,646 bytes，SHA `C303922BF25E71C51F16DF48E9DF972B513D8E463E6F9222A7BDE68245141B1D`。
- grayscale300：89,972 bytes，SHA `509A90CBE56D30705CF63A4044696828A9A6613A1A620C20D1DB9520B44BD6A6`。
- semantic overlay：200,918 bytes，SHA `677884F8A13C3CA3B931259F799F73094A63C27E3F17E4841505453A61573BA1`。
- page integration200：150,833 bytes，SHA `821D5D254CA532866E93C3712CC49397BC3927FF4C7BB7EB756820E46F235188`。
- ROI01 native1x/NN8x：SHA `21A4D01F620F279B94EAE33631C6A8ECA22CD1A64A7A248BB164177F77C9D7B8` / `B39FF4185D8F73E40D7E91E71F0875D5FABD8837BF5A8710DB3DAA7A5C4EFFAA`。
- ROI02 native1x/NN8x：SHA `13CC9DF544AB013CAE77C68029E68AD453033F2EC8A4DD7014277D6F71C77B7D` / `31DA255D9B7353D99FBB4C7BB70E6E151452E0FFD40D27EDE8DA8431FC8F94FB`。
- ROI03 native1x/NN8x：SHA `0A25F90B50BD9F3424852ECFDF70CAC2F362F939D6F449C5ABA13167D7FEE0A2` / `B4013B3844CD7B5EC03D11D0DA6C03525113C4BCE9C9D07BC3083566577D2711`。
- ROI04 native1x/NN8x：SHA `EB8D2850CC4D416F42EB93993D63FCB6AD903BA37EC4AFBF9C966E0CD7A2425E` / `EA9D5109E04CE1C8FD215E5436D5D950637D295DB58281AA1A092C46B026E505`。

主线观察无字体缺损、真实碰撞、裁切、灰度塌缩、panel混读、数学符号错误、题注断裂或页面融合反证。

## 进程边界披露

验收末次只读快照再次可见一个非本P665/P067链启动的外部`latexmk.exe`。主线不查询归属、不管理、不终止，不据此改写已冻结R113/P665身份；所有授权角色继续严格禁止TeX/build/process management，下一角色仍为纯只读SA3。

## 唯一下一角色授权

C 获授权启动一个不同的 completely fresh isolated R113 P665 SA3：

- HANDOFF_ID：`C-FIG-P665-01-R113-SA3-FRESH-ISOLATED-V1`。
- actual instance预期：`/root/sa3_fig_p665_r113_fresh_isolated_v1`。
- model/effort/fork_turns：`gpt-5.6-sol/xhigh/none`。
- new root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa3_r113_fresh_isolated_v1`；授权前主线复核file=false、directory=false、parent=true。

Fresh dispatch只能含official R113、main当前P665单源、root GOAL/direct strict protocol-schema与必要current V5-C05 context。不得暴露或读取本SA1、已接受SA2或任何旧P665的页号、N/C、pair、metric、verdict、acceptance、root/evidence/report/handoff；绝对禁其他UID、Main state/history/acceptance、Git/chat结论及任何agent/thread/task status/identity/history工具。PDF/main/source只读；TeX/build/source/Git/central/process management/second UID/second P665 role=0。

同一fresh instance从零直跑一次sealed PASS/FAIL；PASS仅请求Main C_LOCAL acceptance，不得自计C_LOCAL/global/final pass或自行启动下一UID/role。

P665 `SA1→SA3`；inventory更新为`31 SA1 / 37 SA2 / 2 SA3 / 30 local pass`。P067 R113 fresh SA3同一实例继续：已独立冻结N117/C6786但尚未完成开图/manual，hard status仍open；不得注入P665或旧P067信息。
