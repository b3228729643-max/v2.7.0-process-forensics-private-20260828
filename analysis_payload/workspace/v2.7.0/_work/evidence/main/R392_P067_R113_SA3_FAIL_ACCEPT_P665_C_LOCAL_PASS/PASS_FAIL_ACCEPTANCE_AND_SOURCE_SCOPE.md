# R392：P067 SA3 FAIL接受、P665 C_LOCAL接受与P067最窄静态源范围

- 时间：2026-08-27T19:39:15+08:00。
- 主线：`v2.7.0/integration`，HEAD=`3bc644256d833272a789a7685b91996f98fa3336`，clean。
- 唯一正式候选仍为R113：817页、4,967,121 bytes、SHA-256=`6B48D215721463EA2A9B94EFA54200F8D767B609E47714A70D9B441328F2BB9D`；本轮不构建、不替换PDF。

## P067 fresh SA3 FAIL验收

- 接受HANDOFF=`A-R113-P067-SA3-FRESH-ISOLATED-20260827`，正式路由=`SA3_FAIL_RETURN_TO_SA2`。
- sealed root ordinary854/7,854,378 bytes、dirs13；854/854 files与13/13 dirs含root均ReadOnly。`WRITE_STOPPED`唯一，strict latest margin=106,918,913 NTFS ticks，excluding marker at-or-after=0；JSON4/CSV15 parse failure0，ADS/cache-pyc/reparse0。
- final N130=95 glyph+35 final-visible graphic，另跟踪5 occluder；all unordered C8385。人工账objects130、critical71、views10、typography18、math/semantic12；最终decision仅P01916/P01917为`FAIL_REAL_ILLEGAL_OVERLAP`，其余69项clear/occluded/intentional。
- 两个FAIL均为T016（`p_4`的数学斜体`p`）与G008 CDF y=1 plateau、G009 y=1 dashed reference各34 native300dpi final-visible shared ink，clearance0。主线独立打开两组original1x、nearest8x overlay及intersection mask，确认蓝线穿过黑色`p`顶笔，非bbox、微栅格或背景归属污染。
- R168的18项字体/轮廓数值偏差均为ADVISORY_ONLY；PMF/CDF、右连续、open/filled endpoints、codepoint、灰度、题注与页面融合其余PASS，不能覆盖上述两个真实碰撞。

## P067唯一static-only源范围

- 唯一可写源：`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex`。
- 唯一允许diff：

  `at (axis cs:4.08,.89) {$p_4$};`

  改为

  `at (axis cs:4.08,.85) {$p_4$};`

- x坐标、文本、anchor、mass style、font、fill/opacity、inner sep、CDF/PMF曲线、端点、guides、axes、题注、其他标签与全部其他token必须0变；禁止第二源、TeX/build、commit、fresh role或第二UID。
- 只读静态依据：current native300dpi step rows给出约204px/y-unit；`.04`下移约8px。把T016/T017 final masks下移8px后，与其余128对象的交集为0；最近G008 center distance6px（5 blank px）、G009 distance7px（6 blank px），下一对象距离20.10px。该结果只授权静态补丁，不宣称render PASS；A须回before/after identity、exact diff和静态回归后另请唯一build槽。

## P665 fresh SA3 C_LOCAL验收

- 接受HANDOFF=`C-FIG-P665-01-R113-SA3-FRESH-ISOLATED-V1`并正式计`C_LOCAL_PASS`；P665 source/evidence/roles永久冻结。
- root manifest rows71/payload71、ordinary73；duplicate/missing/extra/path/bytes/SHA/creation+lastwrite FILETIME/attributes mismatch0；73/73 files与3/3 dirs含root只读。marker6物理行/6 unique required keys，strict latest margin=3,868,152,362 ticks，at-or-after0；CSV/JSON parse、ADS/cache-pyc/reparse0。
- fresh N22、all unordered C231/231 unique/self0；machine `COLLISION_MASK_OVERLAP_PX=0`全表。manual pair文档用全表规则闭合并逐ID列出5个near pairs；虽然不是另写231-row manual CSV，主线明确接受该粒度，因为全231行机器集合封闭、规则无unknown，5个风险pair逐项人工裁决，唯一P-O15-O16已打开native1x/NN8x并有7 blank px。
- object O01–O22全部逐ID人工CLEAR；codepoint machine22、manual15个text/formula/caption semantic objects闭合；数学独立复算`A=log B`、`∂A/∂α_k=ψ(α_k)−ψ(α_0)=E[log Θ_k]`及严格Jensen区分正确。主线实际打开figure+caption与R03 native1x/NN8x，无碰撞、裁切、错码或可读性反证。

## 路由与库存

- P067：`SA3→SA2`；P665：`SA3→C_LOCAL_PASS`。
- inventory=`31 SA1 / 38 SA2 / 0 SA3 / 31 local pass`；严格最终0/99，B累计66/66。
- 当前观察到1个外部TeX-family进程；主线不查询归属、不管理或中止。A/C不得启动TeX，P067 build须等待后续显式唯一槽授权。
