# R366 P662 SA1 内容方向接受、原根控制拒收与一次重封授权

时间：2026-08-27T16:40:22+08:00

## P662 内容与视觉方向

- HANDOFF_ID：`C-FIG-P662-01-R112-SA1-FRESH-ISOLATED-V1`；actual instance：`/root/sa1_fig_p662_r112_fresh_isolated_v1`。
- 主线只读复算确认manifest42行与42个payload逐项relative path/bytes/SHA/creation+lastwrite FILETIME零差；ordinary44，44/44文件与10/10目录含root均ReadOnly；JSON/CSV parse、ADS、cache/pyc、reparse均0。
- 台账复算：objects25/25、text ELEMENT_ID21/21、machine pairs300/300 unique、manual pair IDs300/300 unique；manual dispositions恰`281 CLEAR + 16 LEGAL_ENDPOINT + 3 CLEAR_BBOX_ONLY`，illegal/clip/unresolved均0。
- 主线实际打开R112 physical710整页300dpi、彩色/灰度figure+caption、semantic reading-order overlay、input公式与divide/ratio的native1x+nearest8x ROI。Gamma同率归一化、总量与比例独立、`K=2`退化Beta、箭头读序、题注与页面融合均无业务反证。
- 因而业务方向保留为`SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`，但尚不能迁移角色或授权SA3。

## 决定性原根控制拒收

- 原root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa1_r112_fresh_isolated_v1`，永久只读，不原地修补、retimestamp或重封。
- `WRITE_STOPPED`中三个预期`KEY=VALUE`字段被PowerShell数组表达式写坏：`SEALED_ROOT=`、`MANIFEST_ROWS=`、`MANIFEST_SHA256=`均为空值，真实path、`42`与manifest SHA分别掉到下一条无键孤立行。
- 冻结`seal_once.ps1`本来要求从`MANIFEST_SHA256=*`行解析并与实际manifest hash比较；按现有marker解析得到空字符串，故该自引用校验若完整执行必然失败。此前目录attribute setter在marker move前停止，后续手工续行仅做了move与不含该字段语义的机械核验，不能补足此缺口。
- 文件级WSTOP仍唯一且领先其余文件10,000,000 FILETIME ticks；这不能覆盖marker关键字段为空的控制失败。正式裁决：`ROOT_REJECT_MALFORMED_WSTOP_KEY_VALUES`。

## 恰一次 evidence-only sibling 重封授权

- 授权HANDOFF_ID：`C-FIG-P662-01-R112-SA1-FRESH-ISOLATED-CONTROL-RESEAL-V1`。
- 唯一新root：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa1_r112_fresh_isolated_v1_control_reseal_v1`；执行前必须file=false、directory=false。
- 唯一来源为原根manifest绑定的42个material；旧`controls/manifest.csv`与旧`WRITE_STOPPED`复制0。逐项relative path/bytes/SHA/creation+lastwrite FILETIME必须保持同一。
- 新增且仅新增`COPY_IDENTITY.csv`、resolved `COPY_PROVENANCE.json`两个payload，故新payload44；再生成新payload manifest、seal audit、resolved `WRITE_STOPPED`三个controls，最终ordinary47。
- controller与auditor均置于root外，PowerShell7，执行前AST0；controller invocation恰1、retry0。WSTOP构造必须使用无歧义显式字符串格式，预检和根外审计均须逐键断言非空且精确：至少`SEALED_ROOT`、`MANIFEST_ROWS=44`、`MANIFEST_SHA256`、HANDOFF/UID/verdict；禁止无键孤立值、占位符、TAB+`rue`等控制畸形。
- 所有payload/controls/files/dirs/root均ReadOnly；外部marker在全部premarker操作完成后才预制并立即单次move入root作为最后content operation；WSTOP唯一严格晚于其余文件，at-or-after excluding marker0，postmarker content+attribute0。manifest/FS path/bytes/SHA/ticks、copy identity、JSON/CSV、ADS/cache/pyc/reparse均须根外复算0差。
- 禁止重跑PDF/render/视觉/object/pair/manual/数学/语义，禁止TeX/build/source/Git/central写、第二UID/第二P662角色或fresh SA3。仅主线接受新重封根后，才可另行授权different fresh isolated SA3。

## P067 并行边界

- 同一fresh isolated R112 SA3已实际打开6个核心view与17/17 final contact sheets，冻结N130/C8385。
- 当前fresh hard方向为CDF step path相对open/closed endpoints整体左移一段：跳后累计值落在跳前区间，违反PMF到CDF累积关系与右连续语义。该方向与已接受SA1冲突，当前不提前裁决。
- A必须在同一实例/root完成真实逐ID/manual pair/view/semantic账并诚实单次sealed FAIL；不得改源、TeX、restart或另起角色。主线收到sealed结果后再用R112原生图和current source独立裁决。

inventory保持`32 SA1 / 37 SA2 / 1 SA3 / 29 local pass`；main HEAD仍为`27fca4d1a0c9034807a161c1bffa4f4d8f099339`且clean，R112仍为唯一正式候选，TeX0。
