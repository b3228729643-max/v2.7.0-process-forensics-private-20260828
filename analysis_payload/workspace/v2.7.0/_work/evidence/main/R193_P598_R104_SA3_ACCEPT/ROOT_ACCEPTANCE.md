# R193｜FIG-P598-01 R104 fresh isolated SA3 中央接收

- 中央裁决：`ACCEPT_A_LOCAL_PASS`
- HANDOFF_ID：`A-R104-P598-01-SA3-FRESH-ISOLATED-RESTART2-20260825`
- 实例：`/root/p598_01_r104_fresh_sa3_restart2`
- 唯一有效sealed root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-01\STRICT_R4_SA3_FRESH_ISOLATED_R104_R168_RESTART2_20260825`
- R2/R3：均为平台中断的`UNSEALED_INTERRUPTED`根，继续永久禁读、禁写、禁续跑且不得用于裁决。
- 官方候选：R104，物理页649；817页A4，4,967,222 bytes，SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`。

## 一次性中央机械验收

- SA3独立重建N168=142 glyph+26 visible graphic；完整无序pair 14,028/14,028；critical/nearest relationship 19/19。
- 双manifest列出250项；sealed root普通文件252=`payload 248 + 双manifest + SEAL + WSTOP`。manifest path、bytes、SHA-256逐项与文件系统一致，missing/extra 0；sha256清单250/250与JSON一致。
- root payload/controls全只读；ADS、pyc、cache、post-seal write均0；`WSTOP`严格最新。
- 168个对象逐ID人工记录及19个critical关系逐项观察；完整pair overlap/clearance矩阵均已打开。机器输出不含人工决定字段，人工账不是脚本批量生成。
- illegal overlap 0、clip 0、empty mask 0；17个raw intersections均为双圈、锚点、时间轴或shaft-to-own-arrowhead的合法结构接触。

## 中央视觉与语义验收

- 主线已打开200dpi整页、300dpi原生裁图、灰度、完整对象overlay、代表glyph/graphic contact与critical relationship证据。
- 状态序列为`a,b,b,c,c,b,a`，时间标记`t=0,1,2,3,4,5,T`，六条有向转移与连续时间轴完整；相邻重复状态的双圈与虚线相关说明清楚。
- 图中 `K(x_t,dx_{t+1})`、题注 `K(x,dy)` 和 `x→y` 的数学语义、方向与正文一致。
- 字形完整、码点正确、清晰可读；不存在缺字/tofu、真实裁切、非法碰撞或肉眼明显失衡。R168下的细小字号/像素差异仅保留advisory。
- SA1 N164与SA3 N168的差异来自SA3把可见图元分解得更保守；SA3完整覆盖142字形、26图元及全部14,028 pair，没有漏对象或候选漂移。

## 路由

FIG-P598-01正式计入共享第7个`A_LOCAL_PASS`。A可用释放槽启动下一个A独占、未闭环、非冲突UID的fresh只读SA1；不得重启P598、读取R2/R3未封根、启TeX或新增业务源码写者。严格全书最终仍为0/99。
