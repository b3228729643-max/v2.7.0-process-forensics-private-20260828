# FIG-P608-01 R104 / R168 SA2 no-source-change 中央验收

- Revision：202
- HANDOFF_ID：`A-R104-P608-SA2-R168-READONLY-NO-SOURCE-CHANGE-20260826`
- 官方候选：R104物理661 / 印刷648 / 图32.8；817页，4,967,222 bytes，SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- 当前图源SHA-256：`78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`
- 裁决：`ACCEPT / SA2_NO_SOURCE_CHANGE / ROUTE_FRESH_SA1`

## 裁决依据

- 旧R101唯一FAIL为TXT-098面积比`56/61=0.9180327869 < 0.92`，高度比1.0，仅差旧阈值约0.001967。按R168，纯像素比例/旧taxonomy微差为advisory，不能单独触发返源或重建。
- 中央打开R104整页、300dpi彩色/灰度图、关键注释native与8x视图。`t=1,...,5`、`t=6,...,20`、`X_t`、运行均值、target 2、曲线/点/虚线和题注均完整清楚；缺字/tofu、错codepoint/数学语义、实际不可读、明显失衡、真实裁切、非法重叠均为0。
- evidence root payload12 + controls3 = ordinary15；CSV/JSON各12，path/bytes/SHA/mtime五字段到FS差0；15/15只读，ADS/cache/pyc/postseal0，`WRITE_STOPPED`严格最新3,463,700 ticks。
- A worktree该图源无局部差异；本轮TeX、源码修改、提交与第二UID均为0。

## 迁移

- `FIG-P608-01`：SA2 → 完全fresh isolated R104 SA1；无需源码变更或新官方构建。
- inventory：`36 SA1 / 52 SA2 / 1 SA3 / 10 A_LOCAL_PASS`；严格最终仍`0/99`。
- fresh SA1必须新实例/新根，从零审查R104当前页与当前单源，不继承本SA2结论；PASS仍只转另一fresh isolated SA3。

